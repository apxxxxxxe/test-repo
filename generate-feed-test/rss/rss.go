package rss

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
	"time"

	"github.com/gorilla/feeds"
)

type twtyTweet struct {
	Text       string `json:"text"`
	FullText   string `json:"full_text,omitempty"`
	Identifier string `json:"id_str"`
	Source     string `json:"source"`
	CreatedAt  string `json:"created_at"`
	User       struct {
		Name            string `json:"name"`
		ScreenName      string `json:"screen_name"`
		FollowersCount  int    `json:"followers_count"`
		ProfileImageURL string `json:"profile_image_url"`
	} `json:"user"`
	RetweetedStatus *struct {
		FullText string `json:"full_text"`
	} `json:"retweeted_status"`
	Place *struct {
		ID       string `json:"id"`
		FullName string `json:"full_name"`
	} `json:"place"`
	Entities struct {
		HashTags []struct {
			Indices [2]int `json:"indices"`
			Text    string `json:"text"`
		}
		UserMentions []struct {
			Indices    [2]int `json:"indices"`
			ScreenName string `json:"screen_name"`
		} `json:"user_mentions"`
		Urls []struct {
			Indices [2]int `json:"indices"`
			URL     string `json:"url"`
		} `json:"urls"`
	} `json:"entities"`
}

func parseTime(clock string) time.Time {
	const ISO8601 = "2006-01-02T15:04:05+09:00"
	var (
		tm          time.Time
		finalFormat = ISO8601
		formats     = []string{
			ISO8601,
			time.ANSIC,
			time.UnixDate,
			time.RubyDate,
			time.RFC822,
			time.RFC822Z,
			time.RFC850,
			time.RFC1123,
			time.RFC1123Z,
			time.RFC3339,
			time.RFC3339Nano,
		}
	)

	for _, format := range formats {
		if len(clock) == len(format) {
			switch len(clock) {
			case len(ISO8601):
				if clock[19:20] == "Z" {
					finalFormat = time.RFC3339
				} else {
					finalFormat = ISO8601
				}
			case len(time.RubyDate):
				if clock[3:4] == " " {
					finalFormat = time.RubyDate
				} else {
					finalFormat = time.RFC850
				}
			default:
				finalFormat = format
			}
			break
		}
	}

	tm, _ = time.Parse(finalFormat, clock)

	return tm
}

func parseTwtyCmd(args ...string) ([]*twtyTweet, error) {
	args = append([]string{"-json"}, args...)
	jsonData, err := exec.Command("twty", args...).Output()
	if err != nil {
		return []*twtyTweet{}, err
	}

	jsonText := string(jsonData)
	jsonTexts := strings.Split(jsonText, "\n")
	jsonTexts = jsonTexts[0 : len(jsonTexts)-1]

	tweets := make([]*twtyTweet, len(jsonTexts))

	for i, tweetJson := range jsonTexts {
		if err := json.Unmarshal([]byte(tweetJson), &tweets[i]); err != nil {
			fmt.Println(err)
		}
	}

	return tweets, nil
}

func GetFeedFromTwty(title string, args ...string) (string, error) {
	tweets, err := parseTwtyCmd(args...)
	if err != nil {
		return "", err
	}

	now := time.Now()
	feed := &feeds.Feed{
		Title:       title,
		Link:        &feeds.Link{Href: "twty-rss " + strings.Join(args, " ")},
		Description: "",
		Author:      &feeds.Author{Name: "Twitter"},
		Created:     now,
	}

	feed.Items = []*feeds.Item{}

	for _, tweet := range tweets {

		link := fmt.Sprintf("https://twitter.com/%s/status/%s", tweet.User.ScreenName, tweet.Identifier)

		feed.Items = append(feed.Items, &feeds.Item{
			Title:       fmt.Sprint(tweet.User.Name, " / @", tweet.User.ScreenName, " ", tweet.Text),
			Link:        &feeds.Link{Href: link},
			Description: tweet.FullText,
			Created:     parseTime(tweet.CreatedAt),
		})
	}

	rss, err := feed.ToRss()
	if err != nil {
		return "", err
	}

	fmt.Println(rss)

	return rss, nil
}
