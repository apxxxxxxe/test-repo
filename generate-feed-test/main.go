package main

import (
	"errors"
	"fmt"
	"os"

	"github/apxxxxxxe/twty-rss/rss"
)

func main() {
	if len(os.Args) < 3 {
		panic(errors.New(fmt.Sprint("not enough args:", len(os.Args))))
	}
	r, err := rss.GetFeedFromTwty(os.Args[1], os.Args[2:]...)
	if err != nil {
		panic(err)
	}
	fmt.Println(r)
}
