#!/usr/bin/env python
# -*- cording: utf-8 -*-

#Todo:
#・終了時の設定をjsonに書き込む処理
#・リピート設定とシャッフル/順繰り/一曲の設定を別にする
#・再配布可能かつUIに合うフォントの設定
#・おざなりな変数名を修正
#・再生中に再生リストを表示する　再生リストは任意の曲名をクリックしてその再生を開始するように
#・メニュー画面の色をどうするか　スキンの取り扱い
#・データベースの作成　フォルダ構成をそのまま利用する形からソフト内でプレイリストを編集するように
#・対応形式の追加
#・起動・再生のたびに読むと重いのでSQliteで曲の情報を管理するように
#・事前にシャッフル版と順繰り版を作成しておくように
#・次の曲/前の曲切替時に一時停止を解除するかどうか

import pygame.mixer
import pygame.font
import pygame.display
import pygame.time
import os.path
import sys
import glob
import random
import mutagen
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from pygame.locals import *
from io import BytesIO
from PIL import Image
import numpy as np
import scipy.cluster
import logging
import json

# ログレベルを DEBUG に変更
logging.basicConfig(level=logging.DEBUG)

def make_gradation_image(color_gradation, color_background, size_window):
	#指定色に塗りつぶしたimg_colorにアルファ情報img_alphaを載せて目的の形を作る
	img_background = Image.new("RGB", size_window, color_background)
	img_mask = Image.open("graphics/gradation.png").copy().resize(size_window).convert('L')
	img_gradation = Image.new("RGBA", size_window, color_gradation)
	img_background.paste(img_gradation, (0,0), img_mask)
	return pygame.image.frombuffer(img_background.tobytes(), img_background.size, img_background.mode)
	
def middle_color(color1, color2):
	#二色を混ぜて返す
	c1 = np.array(color_code_2_list(color1))
	c2 = np.array(color_code_2_list(color2))
	c = (c1*3 + c2*7) // 10
	return '#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2])

def color_code_2_list(color_code):
	#カラーコードを配列に分解する
	r = int(color_code[1:3], 16)
	g = int(color_code[3:5], 16)
	b = int(color_code[5:7], 16)
	return [r,g,b]

#k平均法で画像のドミナントカラーを1つ以上求める
def kmeans_process(img, n_cluster):
    sm_img = img.resize((100, 100)) #画像を縮小して負荷を軽減
    color_arr = np.array(sm_img)
    w_size, h_size, n_color = color_arr.shape
    color_arr = color_arr.reshape(w_size * h_size, n_color)
    color_arr = color_arr.astype(np.float)

    codebook, distortion = scipy.cluster.vq.kmeans(color_arr, n_cluster)  # クラスタ中心
    code, _ = scipy.cluster.vq.vq(color_arr, codebook)  # 各データがどのクラスタに属しているか

    n_data = []  # 各クラスタのデータ数
    for n in range(n_cluster):
        n_data.append(len([x for x in code if x == n]))

    desc_order = np.argsort(n_data)[::-1]  # データ数が多い順

    return ['#{:02x}{:02x}{:02x}'.format(*(codebook[elem].astype(int))) for elem in desc_order]

def recreate_playlist(i_playing, play_mode, files):
	if play_mode == 0:	#shuffle 再生時点以降のプレイリストをシャッフル
		#現在地から後ろを切り出してシャッフルして連結　インデックスはそのまま
		tmp_files = files[i_playing+1: len(files)]
		random.shuffle(tmp_files)
		final_files = files[: i_playing+1] + tmp_files
		final_index = i_playing
	elif play_mode == 1:
		#昇順にソートして現在曲のインデックスを合わせる
		final_files = sorted(files)
		final_index = final_files.index(files[i_playing])
	else:
		final_files = files
		final_index = i_playing
	return final_files, final_index

def set_screen(flg_folded, flg_fullscreen, size_display):
	#フルスクリーンからウィンドウに戻すとタイトルバーが消える不具合あり
	if not flg_fullscreen:
		if flg_folded:
			size_window = [300, 100]
		else:
			size_window = [600, 400]
		screen = pygame.display.set_mode(size_window, 0)
	else:
		size_window = size_display
		screen = pygame.display.set_mode((0, 0), FULLSCREEN)
	return screen, size_window

def get_music_length(filepath):
	#mp3, aac, m4a, flacファイルから曲の長さを返す関数
	filename = os.path.split(filepath)[1]
	filename, ext = os.path.splitext(filename)
	ext = ext.lower()
	try:
		if ext == ".mp3":
			return MP3(filepath).info.length
		if ext in ["aac", ".m4a"]:
			return MP4(filepath).info.length
		if ext == ".flac":
			return FLAC(filepath).info.length
	except Exception as e:  # 応急処置的に全エラーを拾ってる…後で修正すること
		logging.error("get_music_length エラー: %s" % e)
		return filename

#mp3, aac, m4a, flacファイルから曲のタイトルを返す関数
def get_music_album(filepath):
	filename = os.path.split(filepath)[1]
	filename, ext = os.path.splitext(filename)
	foldername = os.path.basename(os.path.dirname(filepath))
	try:
		if ext == ".mp3":
			return MP3(filepath).tags["TALB"][0]
		if ext in ["aac", ".m4a"]:
			return MP4(filepath).tags["\xa9alb"][0]
		if ext == ".flac":
			return FLAC(filepath).tags["album"][0]
	except KeyError as e:
		logging.warning("Keyerror: {0}にはアルバム情報がない".format(filename))
		return foldername
	except TypeError as e:
		logging.error("TypeError: {0}には")
		return foldername

#mp3, aac, m4a, flacファイルから曲のタイトルを返す関数
def get_music_title(filepath):
	filename = os.path.split(filepath)[1]
	filename, ext = os.path.splitext(filename)
	ext = ext.lower()
	try:
		if ext == ".mp3":
			return MP3(filepath).tags["TIT2"][0]
		if ext in ["aac", ".m4a"]:
			return MP4(filepath).tags["\xa9nam"][0]
		if ext == ".flac":
			return FLAC(filepath).tags["title"][0]
	except KeyError as e:
		logging.warning("Keyerror: {0}にはタイトル情報がない".format(filename))
		return filename
	except TypeError as e:
		logging.error("TypeError: {0}には")
		return filename

# 文字列が画面に収まるようにお尻を削る
def abb_string(string, font, sizex_screen):
	if font.size(string)[0] >= sizex_screen:
		while True:
			if font.size(string)[0] < sizex_screen:
				#余白を作るため最後は多めに削る
				string = "%s..." %string[:-3]
				#string = string[:-3]
				break
			else:
				string = string[:-1]
	return string

#白黒画像を指定した色に変えて画像サーフェスを返す
def recolor_buttons(images, dst_color, bairitu):
	img_surface = []
	for imgpath in images:
		#指定色に塗りつぶしたimg_colorにアルファ情報img_alphaを載せて目的の形を作る
		img_alpha = Image.open(imgpath).copy().convert('L')
		img_color = Image.new("RGB", img_alpha.size, dst_color)
		img_color.putalpha(img_alpha)
		img_middle = pygame.image.frombuffer(img_color.tobytes(), img_color.size, img_color.mode)
		img_surface.append(pygame.transform.scale(img_middle, (int(img_color.size[0] * bairitu), int(img_color.size[1] * bairitu))))
	return img_surface

def is_true(string):
	return string.lower() == 'true'

#メイン処理--------------------------------------------------------------------------------------------------

def main():
	dic_config = json.load(open("config.json", 'r'))

	play_mode = int(dic_config['playmode'])				# 再生モード 0: シャッフル 1: 順繰り 2: 一曲リピート
	flg_autoplay = is_true(dic_config["autoplay"])		# 起動したら自動的に再生を開始するフラグ
	flg_folded = is_true(dic_config["folded"])			# コンパクト表示フラグ
	default_artist = str(dic_config["defaultartist"])	# 自動再生するプレイリストのフォルダ名(無効な名前ならランダム)
	flg_fullscreen = is_true(dic_config["fullscreen"])	# フルスクリーンで起動するフラグ
	flg_gradation = is_true(dic_config["gradation"])	# 再生画面の背景にグラデーション効果をつけるフラグ
	bairitu = float(dic_config['bairitu'])
	font_size = int(float(dic_config['fontsize']) * bairitu)			# フォントサイズ
	font_name = str(dic_config['fontname'])				# フォント名
	yoin_time = int(dic_config['yointime'])				# フォントサイズ
	flg_debug = is_true(dic_config["debug"])

	tick = 50	# ループ中のウェイト(ms)
	height = int(180 * bairitu) # アルバムアートの高さ

	last_play_mode = play_mode
	# pygameモジュールの初期化
	pygame.mixer.init()
	pygame.display.init()
	pygame.font.init()

	size_display = [pygame.display.Info().current_w, pygame.display.Info().current_h]
	screen, size_window = set_screen(flg_folded, flg_fullscreen, size_display)  # 画面を作成

	color_menu_text = [104,104,104]
	color_menu_background = [170,170,170]
	pygame.mixer.music.set_endevent(pygame.USEREVENT)	# 各曲の再生が終了したときのイベントを作成
	skin = "Monotone"
	icon = pygame.image.load("graphics/%s/icon.png" % skin)
	pygame.display.set_icon(icon)
	title_bar = "musicplayer.py"
	pygame.display.set_caption(title_bar)  # タイトルを作成
	font_small = pygame.font.Font("fonts/{0}".format(font_name), font_size//2)
	font_number = pygame.font.Font("fonts/{0}".format(font_name), font_size)
	font_bold = pygame.font.Font("fonts/{0}".format(font_name), font_size)
	font = pygame.font.Font("fonts/{0}".format(font_name), font_size)
	player_images = [
		"graphics/%s/buttonPlay.png" % skin,
		"graphics/%s/buttonPause.png" % skin,
		"graphics/%s/buttonNext.png" % skin,
		"graphics/%s/buttonPrev.png" % skin,
		"graphics/%s/ProgressBar.png" % skin,
		"graphics/%s/ProgressIcon.png" % skin,
		"graphics/%s/arrowUp.png" % skin,
		"graphics/%s/arrowDown.png" % skin
	]
	player_sub_images = [
		"graphics/%s/buttonPlayModeShuffle.png" % skin,
		"graphics/%s/buttonPlayModeNormal.png" % skin,
		"graphics/%s/buttonPlayModeSingleloop.png" % skin,
		"graphics/%s/buttonPlayModeSingle.png" % skin,
	]
	player_subsub_images = [
		"graphics/%s/buttonBack.png" % skin
	]

	img_button_arrowUp = pygame.image.load("graphics/%s/arrowUp.png" % skin)
	img_button_arrowDown = pygame.image.load("graphics/%s/arrowDown.png" % skin)

	while True:
		#プレイリスト選択の開始--------------------------------------------------------------
		screen, size_window = set_screen(False, flg_fullscreen, size_display) #強制的に展開表示
		pygame.display.set_caption(title_bar)

		artists = glob.glob("./playlists/*/")
		len_artists = len(artists)

		if len_artists == 0:
			logging.error("playlistフォルダからフォルダを検索できませんでした")
			sys.exit()
		if len_artists == 1:
			number = 0
		elif flg_autoplay:
			#  自動再生が有効のとき、最初に再生するアーティストのインデックスを取得する
			#  指定のアーティストが見つからなかった場合はランダム
			try:
				number = artists.index("./playlists\\{0}\\".format(default_artist))
			except ValueError:
				number = random.randrange(len_artists)
		else:
			# playlistsフォルダ内のディレクトリ一覧を表示して選択オプションを出す
			pos_y_scroll = 0
			flg_decided = False
			str_artists = []
			for i in range(len_artists):
				str_artists.append(os.path.basename(os.path.dirname(artists[i])))
			flg_display_update = True
			while not flg_decided:
				if flg_display_update:
					flg_display_update = False
					screen.fill(color_menu_background)  # 画面を塗りつぶす
					screen.blit(font_bold.render("プレイリスト", True, color_menu_text), [10, 10])
					pos_button_arrow = (size_window[0] - 10 - 9, size_window[1] - 10 - 5)
					if not flg_folded:
						screen.blit(img_button_arrowUp, pos_button_arrow)
					else:
						screen.blit(img_button_arrowDown, pos_button_arrow)
					rect_button_arrow = pygame.Rect([pos_button_arrow[0] - 10, pos_button_arrow[1] - 10, 9 + 20, 5 + 20])
					ren_artists = [0] * len_artists
					rects_artist = [0] * len_artists
					# プレイリスト名を一覧で出す
					for i in range(pos_y_scroll, min(pos_y_scroll + size_window[1] // font_size - 1, len_artists)):
						ren_artists[i] = (font.render(str_artists[i], True, color_menu_text))
						pos_artists = ((size_window[0] - ren_artists[i].get_width()) / 2, 10 + font_size + 10 + (i - pos_y_scroll)*font.size(str_artists[0])[1])
						rects_artist[i] = (pygame.Rect(pos_artists + font.size(str_artists[i])))
						screen.blit(ren_artists[i], pos_artists)
					pygame.display.update()  # 描画処理を実行
				# ユーザー入力を取得
				for event in pygame.event.get():
					# 終了イベント
					if event.type == QUIT:
						playing = False
						pygame.quit()
						sys.exit()
					# マウスイベント
					if event.type == pygame.MOUSEBUTTONDOWN:
						flg_display_update = True
						# logging.info(event.button)
						if event.button == 3:
							playing = False
							pygame.quit()
							sys.exit()
						elif event.button == 4:
							pos_y_scroll -= event.button//4
							if pos_y_scroll < 0:
								pos_y_scroll = 0
						elif event.button == 5:
							if len_artists > size_window[1] // font.size(str_artists[0])[1] + 1:
								pos_y_scroll += event.button//5
								if pos_y_scroll > len_artists - size_window[1] // font.size(str_artists[0])[1] + 1:
									pos_y_scroll = max(size_window[1] // font.size(str_artists[0])[1], len_artists - size_window[1] // font.size(str_artists[0])[1]) + 1
						elif rect_button_arrow.collidepoint(event.pos):
							flg_folded = not flg_folded
							screen, size_window = set_screen(flg_folded, flg_fullscreen, size_display)  # 画面を作成
						elif event.button == 1:
							for j in range(pos_y_scroll, min(pos_y_scroll + size_window[1] // font.size(str_artists[0])[1] - 1, len_artists)):
								if rects_artist[j].collidepoint(event.pos):
									number = j
									flg_decided = True
					#キーボードイベント
					elif event.type == KEYDOWN:
						flg_display_update = True
						if event.key == K_F11:
							pos_y_scroll = 0
							flg_fullscreen = not flg_fullscreen
							screen, size_window = set_screen(flg_folded, flg_fullscreen, size_display)  # 画面を作成				pygame.time.wait(tick)
		targetArtist = artists[number]
		targetplaylist = os.path.basename(os.path.dirname(targetArtist))
		flg_autoplay = False

		#プレイリスト選択後　曲再生の準備--------------------------------------------------------------

		screen, size_window = set_screen(flg_folded, flg_fullscreen, size_display)
		# 選択したディレクトリの音楽ファイルを取得
		files = []
		exts = ["flac", "mp3"]
		for e in exts:
			for file in glob.glob(targetArtist+"**/*."+e):
				filename = os.path.split(file)[1]
				filename, ext = os.path.splitext(filename)
				ext = ext.lower()
				#[ファイルパス, ディレクトリ名（アルバム名）, ファイル名（曲名）, 拡張子]
				files.append([file, get_music_album(file), filename, ext])
		#logging.info("\n%s: %d musics" %(targetArtist.replace("./playlists", "").replace("\\", ""), len(files)))

		# 曲順をシャッフル
		if play_mode == 0:
			random.shuffle(files)
		#fixed_files = random_files = files
		#random.shuffle(random_files)

		flg_pause = False
		sec_jump_to = 0	#シークバー操作でジャンプする先の再生時間(sまたは ms)
		index_playing = 0 

		#曲再生の準備--------------------------------------------------------------
		while index_playing < len(files):

			#必要に応じてプレイリストの再生順を再構成
			if not sec_jump_to and play_mode != last_play_mode:
				last_play_mode = play_mode
				files, index_playing = recreate_playlist(index_playing, play_mode, files)
			
			# アルバムアートを取得して色を取得
			flg_no_image = False
			audio = mutagen.File(files[index_playing][0])
			album_images = []
			if 'audio/mp3' in audio.mime:
				album_images = [audio[i] for i in audio if "APIC" in i]
			elif 'audio/flac' in audio.mime:
				album_images = audio.pictures
			else:
				flg_no_image = True

			if len(album_images) == 0 or flg_no_image:
				img_jacket = pygame.image.load("graphics/noimage.png")
				color_background = "#a0a0a0"
				color_text = "#505050"
			else:
				img = Image.open(BytesIO(album_images[0].data))
				width = round(img.width * height / img.height)
				img = img.resize((width, height))
				mode = img.mode
				size = img.size
				data = img.tobytes()
				img_jacket = pygame.image.frombuffer(data, size, mode)
				color_background, color_text = kmeans_process(img, 2)

			#アルバムアートから取得した色を各種ボタン類に適用
			img_button_play, \
			img_button_pause, \
			img_button_next, \
			img_button_prev, \
			img_progress_bar, \
			img_progress_icon, \
			img_button_arrowUp, \
			img_button_arrowDown = recolor_buttons(player_images, color_text, bairitu)

			if flg_gradation:
				img_button_back = recolor_buttons(player_subsub_images, color_background, bairitu)[0]
			else:
				img_button_back = recolor_buttons(player_subsub_images, color_text, bairitu)[0]

			color_mean = middle_color(color_text, color_background)
			img_buttonplay_mode_shuffle, \
			img_buttonplay_mode_normal, \
			img_buttonplay_mode_singleloop, \
			img_buttonplay_mode_single = recolor_buttons(player_sub_images, color_mean, bairitu)

			#アルバムアートから取得した色で背景Surfaceを作る
			if flg_gradation:
				img_background = make_gradation_image(color_mean, color_background, size_window)
			else:
				img_background = pygame.Surface(size_window)
				img_background.fill(color_background)

			# 再生中に表示する情報の準備
			# 変数extまわりがきちゃない　後で修正
			ext = files[index_playing][3]
			pygame.display.set_caption("[%d/%d] %s" %(index_playing+1, len(files), targetplaylist))
			#str_target_album= ("%s [%d/%d]" %(targetplaylist, index_playing+1, len(files)))
			str_target_album= abb_string(files[index_playing][1], font, size_window[0])
			ren_playlist = font.render(str_target_album, True, color_text)
			strTitle = abb_string(get_music_title(files[index_playing][0]), font_bold, size_window[0])
			ren_title = font_bold.render(strTitle, True, color_text)
			ren_progress_time = font_number.render(("--- / ---"), True, color_text)
			#logging.info("%d. %s" %(i+1 , strTitle))
			# 音楽ファイルの読み込み
			pygame.mixer.music.load(files[index_playing][0])
			msec_progress = 0
			if not sec_jump_to:
				msec_progress_offset = 0
				pygame.mixer.music.play(1, 0.0)
			else:
				msec_progress_offset = sec_jump_to * 1000
				pygame.mixer.music.play(1, sec_jump_to)
			if flg_pause:
				pygame.mixer.music.pause()
			sec_jump_to = 0
			music_length = get_music_length(files[index_playing][0])
			str_music_length = "%d:%s" % (music_length//60, str(int(music_length % 60)).zfill(2))
			ren_music_length = font_number.render(str_music_length, True, color_text)
			playing = True
			flg_display_update = True
			# 曲を順に再生
			while playing:
				#if not flg_pause:
				msec_progress = pygame.mixer.music.get_pos() + msec_progress_offset
				pygame.time.wait(tick)
				if flg_display_update:
					#if flg_folded:
						#flg_display_update = False	#必要になるまで縮小モードでは画面の更新を停止
					str_progress = "%d:%s" % (msec_progress//60000, str(int(msec_progress//1000 % 60)).zfill(2))
					#str_progress = str(msec_progress_offset)
					ren_progress_time = font_number.render(str_progress, True, color_text)
					posx = size_window[0]/2 - 300	#基準になる座標
					posy = size_window[1]/2 - 100
					if flg_folded:
						# 縮小表示時の座標
						pos_button_pause = (posx + (600-48)/2, size_window[1]//7*5 - 16)
						pos_button_next = (pos_button_pause[0]+60, pos_button_pause[1])
						pos_button_prev = (pos_button_pause[0]-(60), pos_button_pause[1])
						#pos_playlist = (posx + 300 - font.size(str_target_album)[0]/2, posy + 30)
						#pos_title = (posx + 300 - font_bold.size(strTitle)[0]/2, pos_playlist[1] + font_size*1.5)
						pos_title = (posx + 300 - font_bold.size(strTitle)[0]/2, size_window[1]//7*2 - font_size/2)
						pos_button_arrow = (size_window[0] - 10 - 9, size_window[1] - 10 - 5)
						rect_buttonplay_mode = pygame.Rect(0, 0, 0, 0)
						rect_progress_bar = pygame.Rect(0, 0, 0, 0)
						rect_button_back = pygame.Rect(0, 0, 0, 0)
					else:
						pos_playlist = (posx + 300 - ren_playlist.get_width()/2, size_window[1] / 2)
						pos_title = (posx + 300 - ren_title.get_width()/2, pos_playlist[1] + font_size*1.8)
						pos_progress_bar = ((size_window[0] - img_progress_bar.get_width())/2, pos_title[1] + font_size*2.5)
						pos_progress_icon = (pos_progress_bar[0] + ((msec_progress/1000) / music_length) * img_progress_bar.get_width() - 2, pos_progress_bar[1] - 5*bairitu)
						pos_button_pause = ((size_window[0] - img_button_pause.get_width())/2, pos_progress_bar[1] + 30)
						pos_button_next = (pos_button_pause[0]+60, pos_button_pause[1])
						pos_button_prev = (pos_button_pause[0]-(60), pos_button_pause[1])
						pos_buttonplay_mode = (pos_button_next[0] + img_button_next.get_width(), pos_button_pause[1] + (img_button_pause.get_height() - img_buttonplay_mode_normal.get_height())/2)
						pos_button_back = (10, 10)
						pos_button_arrow = (size_window[0] - img_button_arrowUp.get_width() - 10, size_window[1] - img_button_arrowUp.get_height() - 10)
						pos_progress_time = [pos_progress_bar[0] - ren_progress_time.get_width() - font_size, pos_progress_bar[1] - ren_progress_time.get_height()/2]
						posmusic_length = [pos_progress_bar[0] + img_progress_bar.get_width() + font_size, pos_progress_time[1]]
						# マウスの当たり判定
						rect_buttonplay_mode = pygame.Rect(pos_buttonplay_mode + img_buttonplay_mode_normal.get_size())
						rect_progress_bar = pygame.Rect([pos_progress_bar[0], pos_progress_bar[1]-10, img_progress_bar.get_width(), 10+img_progress_bar.get_height()+10])#上下に+10ピクセル
						rect_button_back = pygame.Rect(pos_button_back + img_button_back.get_size())

					# マウスの当たり判定
					rect_button_pause = pygame.Rect(pos_button_pause + img_button_pause.get_size())
					rect_button_next = pygame.Rect(pos_button_next + img_button_pause.get_size())
					rect_button_prev = pygame.Rect(pos_button_prev + img_button_pause.get_size())
					rect_button_arrow = pygame.Rect([pos_button_arrow[0] - 10, pos_button_arrow[1] - 10, (9 + 20)*bairitu, (5 + 20)*bairitu])


					#screen.fill(color_background)  # 画面を塗りつぶす
					screen.blit(img_background, (0,0))

					
					# デバッグ用　プレイリスト一覧を表示
					if flg_debug and not flg_folded and flg_fullscreen:
						for p in range(len(files)):
							ren_ps =  font_small.render(files[p][2], True, color_mean)
							screen.blit(ren_ps, ((p == index_playing)*10 + 5, 50 + (font_size/2 + 5)*p))

					#pygame.draw.rect(screen, (255, 0, 0), rect_button_pause)
					#pygame.draw.rect(screen, (255, 0, 0), rect_button_next)
					#pygame.draw.rect(screen, (255, 0, 0), rect_button_prev)
					#pygame.draw.rect(screen, (255, 0, 0), rect_button_back)
					#pygame.draw.rect(screen, (255, 0, 0), rect_buttonplay_mode)
					#pygame.draw.rect(screen, (255, 0, 0), rect_progress_bar)
					#pygame.draw.rect(screen, (255, 0, 0), rect_button_arrow)

					# デバッグ用
					#CenterCheck = pygame.Rect((0,0,size_window[0]/2, size_window[1]/2)); CenterCheck2 = pygame.Rect((size_window[0]/2,size_window[1]/2,size_window[0]/2, size_window[1]/2))
					#pygame.draw.rect(screen, (170, 160, 140), CenterCheck) ; pygame.draw.rect(screen, (170, 160, 140), CenterCheck2)
					#rect_title = pygame.Rect(pos_title + (font_bold.size(strTitle)[0]/2, font_bold.size(strTitle)[1]))
					#pygame.draw.rect(screen, (255, 0, 0), rect_title)

					if not flg_folded:
						if play_mode == 0:
							screen.blit(img_buttonplay_mode_shuffle, pos_buttonplay_mode)
						elif play_mode == 1:
							screen.blit(img_buttonplay_mode_normal, pos_buttonplay_mode)
						elif play_mode == 2:
							screen.blit(img_buttonplay_mode_singleloop, pos_buttonplay_mode)
						else:
							screen.blit(img_buttonplay_mode_single, pos_buttonplay_mode)
						screen.blit(ren_playlist, pos_playlist)
						#screen.blit(img_progress_bar, pos_progress_bar)
						#screen.blit(img_progress_icon, pos_progress_icon)
						pygame.draw.line(screen, color_mean, pos_progress_bar, (pos_progress_bar[0] + 360*bairitu, pos_progress_bar[1]))
						pygame.draw.ellipse(screen, color_text, pos_progress_icon + (int(5*bairitu), int(10*bairitu)))
						screen.blit(img_button_back, pos_button_back)
						screen.blit(ren_progress_time, pos_progress_time)
						screen.blit(ren_music_length, posmusic_length)
						screen.blit(img_button_arrowUp, pos_button_arrow)
						screen.blit(img_jacket, ((size_window[0]-img_jacket.get_rect().size[0])/2, pos_playlist[1] - height - font_size ))
					else:
						screen.blit(img_button_arrowDown, pos_button_arrow)

					# 再生中と停止中でボタンの画像を変える
					if flg_pause:
						screen.blit(img_button_play, pos_button_pause)
					else:
						screen.blit(img_button_pause, pos_button_pause)

					screen.blit(img_button_next, pos_button_next)
					screen.blit(img_button_prev, pos_button_prev)
					screen.blit(ren_title, pos_title)
					pygame.display.update()  # 描画処理を実行
				# キー入力を取得
				for event in pygame.event.get():
					# 曲が一周したとき
					if event.type == pygame.USEREVENT:
						pygame.time.wait(yoin_time*1000)
						if play_mode == 0 or play_mode == 1:
							index_playing += 1
						elif play_mode == 3:
							flg_pause = True
						playing = False
					# ウィンドウを閉じたとき
					if event.type == QUIT:
						playing = False
						pygame.quit()
						sys.exit()
					# マウスイベント
					if event.type == pygame.MOUSEBUTTONDOWN:
						# マウス右or戻るボタンでプレイリスト選択へ
						if event.button == 3 or (event.button == 1 and rect_button_back.collidepoint(event.pos)):
							index_playing = len(files)
							playing = False
							pygame.mixer.music.stop()	#消すなら再生画面に戻れる機能も付けること
						elif event.button == 1:
							if rect_button_pause.collidepoint(event.pos):
								flg_display_update = True
								if not flg_pause:
									pygame.mixer.music.pause()
								else:
									pygame.mixer.music.unpause()
								flg_pause = not flg_pause
							elif rect_button_next.collidepoint(event.pos):
								index_playing += 1
								#flg_pause = False	#どっちの挙動がいいか考える
								playing = False
								if index_playing == len(files) : pygame.mixer.music.stop()
							elif rect_button_prev.collidepoint(event.pos):
								# 曲が始まって2秒以内なら前の曲
								if msec_progress / 1000 < 2 and index_playing > 0:
									index_playing -= 1
								playing = False
								#flg_pause = False	#どっちの挙動がいいか考える
							elif rect_progress_bar.collidepoint(event.pos):
								sec_jump_to = int(((event.pos[0] - pos_progress_bar[0]) / img_progress_bar.get_width()) * music_length)
								if ext == "mp3" or ext == "ogg":
									sec_jump_to *= 1000
								playing = False
							elif rect_button_arrow.collidepoint(event.pos):
								flg_display_update = True
								flg_folded = not flg_folded
								screen, size_window = set_screen(flg_folded, flg_fullscreen, size_display)  # 画面を作成
								if flg_gradation:
									img_background = make_gradation_image(color_mean, color_background, size_window)
								else:
									img_background = pygame.Surface(size_window)
									img_background.fill(color_background)
								if not flg_fullscreen:
									str_target_album= abb_string(files[index_playing][1], font, size_window[0])
									ren_playlist = font.render(str_target_album, True, color_text)
									strTitle = abb_string(get_music_title(files[index_playing][0]), font_bold, size_window[0])
									ren_title = font_bold.render(strTitle, True, color_text)
							elif rect_buttonplay_mode.collidepoint(event.pos):
								play_mode += 1
								if play_mode > 3:
									play_mode = 0
					elif event.type == KEYDOWN:
						if event.key == K_SPACE:
							if not flg_pause:
								pygame.mixer.music.pause()
							else:
								pygame.mixer.music.unpause()
							flg_pause = not flg_pause
						elif event.key == K_F11:
							flg_fullscreen = not flg_fullscreen
							screen, size_window = set_screen(flg_folded, flg_fullscreen, size_display)  # 画面を作成
							if flg_gradation:
								img_background = make_gradation_image(color_mean, color_background, size_window)
							else:
								img_background = pygame.Surface(size_window)
								img_background.fill(color_background)



if __name__ == '__main__':
	main()
