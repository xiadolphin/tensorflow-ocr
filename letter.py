# coding=utf-8
from random import randint
from PIL import Image, ImageDraw, ImageFont
import os
# import os.path
import numpy
import numpy as np
from sys import platform
from extensions import *

# overfit = False
overfit = True
if overfit:
	print("using OVERFIT DEBUG DATA!!!")
	min_size = 24
	max_size = 24
	max_padding = 8
	max_angle = 0
else:
	min_size = 8  # 8#12
	max_size = 32  # street view size, above that: scale image down!
	max_padding=10
	max_angle=45 #! +90deg. with lower probability! see (SVHN) Dataset

shift_up = 9 # pull small letters up
shift_left = 2 #
min_char = 32 # still keep ascii[0-32] for special data: 'white' 'black' 'noise' background line! unicode
offset = 32 #0  # vs min_char keep ascii[0-32] for special data

sizes=range(min_size,max_size)
if min_size==max_size: sizes=[min_size]
letterz= list(map(chr, range(min_char, 128)))
nLetters=len(letterz)


def find_fonts():
	if platform == "darwin":
		os.system("mdfind -name '.ttf' | grep '.ttf$' |grep -v 'Noto\|NISC' > fonts.list")
	else:
		os.system("locate '.ttf' | grep '.ttf$' |grep -v 'mstt' > fonts.list")

# copy all 'good' fonts to one directory if you want
# os.system("mkdir -p "+fonts_dir)

# fonts={} # cache all?
def check_fonts():
	for font in fontnames:
		try:
			if not '/' in font :
				ImageFont.truetype(fonts_dir+font, max_size)
				ImageFont.truetype(fonts_dir+font, min_size)
			else:
				ImageFont.truetype(font, max_size)
				ImageFont.truetype(font, min_size)
		except:
			# print("BAD font "+font)
			fontnames.remove(font)

if not os.path.exists("fonts.list"):
	print("Building fonts.list")
	find_fonts()
else:
	print("Using cashed fonts.list")

fonts_dir="/data/fonts/"
fontnames=readlines("fonts.list")
# check_fonts()
check_fonts()
if overfit:
	fontnames=fontnames[0:1] # ONLY 2 to overfit

if overfit:
	fontnames=['Menlo.ttc']#Arial.ttf']


styles=['regular','light','medium','bold','italic']
# Regular Medium Heavy Demi 'none','normal', Subsetted Sans #,'underline','strikethrough']

from enum import Enum



class Target(Enum):  # labels
	letter = 1
	size = 2
	color = 3
	font = 4
	position = 5
	style = 6
	angle = 7

#
class Kind(Enum):
	blank = 0
	letter = 1
	digit = 2  # special! e.g. House Numbers
	background = 3
	line = 4
	emoji = 5  # special icons
	colour_image = 6
	black_and_white_image = 7
	icon = 8  # 'save', favicons etc
	latin = 9  # åµ ...
	unicode = 10  # special :
	arabic = 11
	chinese = 12  # also korean, japan ...
	cyril = 13


nClasses={
	Target.letter: nLetters,  # classification
	Target.font: len(fontnames),  # classification
	Target.style: len(styles),  # classification
	Target.size: 1,  # max_size # regression
	Target.angle: 1,  # max_angle # regression
	Target.position: 2,  # x,y # regression
	Target.color: 3,  # RGB # regression
	# Target.invert: 1,  # -1 0 1
	# Target.mean: 1,  # -1 0 1
}

# test_word=9 # use 5 even for speaker etc


def pos_to_arr(pos):
	return [pos['x'],pos['y']]


class batch():

	def __init__(self, batch_size=64,target=Target.letter):
		self.batch_size=batch_size
		self.target= target
		self.shape=[max_size * max_size+extra_y, nClasses[target]]
		# self.shape=[batch_size,max_size,max_size,len(letters)]
		self.train= self
		self.test = self
		self.test.images,self.test.labels = self.next_batch()

	def next_batch(self,batch_size=None):
		letters=[letter() for i in range(batch_size or self.batch_size)]
		def norm(letter):
			return letter.matrix()
		xs=map(norm, letters) # 1...-1 range
		if self.target==Target.letter: ys=[one_hot(l.ord,nLetters,offset) for l in letters]
		if self.target == Target.size: ys = [l.size for l in letters]
		if self.target == Target.position: ys = [pos_to_arr(l.pos) for l in letters]
		return list(xs), list(ys)

def pick(xs):
	return xs[randint(0,len(xs)-1)]


def one_hot(item, num_classes,offset):
	labels_one_hot = numpy.zeros(num_classes)
	labels_one_hot[item-offset] = 1
	return labels_one_hot

class letter():
	# fonts=
	# font=property(get_font,set_font)
	# number=property(lambda self:ord(self.char))


	def __init__(self, *margs, **args): # optional arguments
		if not args:
			if margs: args=margs[0] # ruby style hash args
			else:args={}
		# super(Argument, self).__init__(*margs, **args)
		# self.name = args['name']		if 'name' in args else None
		# self.family = args['family'] if 'family' in args else pick(families)
		self.font = args['font'] if 'font' in args else pick(fontnames)
		self.size = args['size'] if 'size' in args else pick(sizes)
		self.char = args['char'] if 'char' in args else pick(letterz)
		self.back = args['back'] if 'back' in args else None #self.random_color() # 'white' #None #pick(range(-90, 180))
		self.ord	= args['ord'] if 'ord' in args else ord(self.char)
		self.pos	= args['pos'] if 'pos' in args else {'x':pick(range(0,max_padding)),'y':pick(range(0, max_padding))}
		self.angle= args['angle'] if 'angle' in args else 0#pick(range(-max_angle,max_angle))
		self.color= args['color'] if 'color' in args else 'black'#'white'#self.random_color() #  #None #pick(range(-90, 180))
		self.style= args['style'] if 'style' in args else self.get_style(self.font)# pick(styles)
		self.invert=args['invert'] if 'invert' in args else pick([-1,0,1])

	# self.padding = self.pos

	def projection(self):
		return self.matrix(),self.ord

	def random_color(self):
		r=randint(0,255)
		g=randint(0,255)
		b=randint(0,255)
		a=randint(0,255)
		return (r,g,b,a)

	def get_style(self,font):
		if 'BI' in font: return 'bold&italic'
		if 'IB' in font: return 'bold&italic'
		if 'BoldItalic' in font: return 'bold&italic'
		if 'Black' in font: return 'bold' #~
		if 'Bol' in font: return 'bold'
		if 'bold' in font: return 'bold'
		if 'Bd' in font: return 'bold'
		if 'B.' in font: return 'bold'
		if 'B-' in font: return 'bold'
		if '_RB' in font: return 'bold'
		# if '-B' in font: return 'bold'
		# if '_B' in font: return 'bold'
		if 'Ita' in font: return 'italic'
		if 'It.' in font: return 'italic'
		if 'I.' in font: return 'italic'
		if 'I-' in font: return 'italic'
		if '_RI' in font: return 'italic'
		if 'Demi' in font: return 'medium'
		if 'Medi' in font: return 'medium'
		if 'Light' in font: return 'light'
		if 'Lt.' in font: return 'light'
		if 'Thin' in font: return 'light'
	# Mono
		return 'regular'

	def matrix(self, normed=true):
		matrix = np.array(self.image())
		if normed: matrix=matrix/ 255.
		if self.invert == -1:
			matrix = 1 - 2 * matrix # -1..1
		elif self.invert:
			matrix = 1 - matrix # 0..1
		return matrix
		# except:
		# 	return np.array(max_size*(max_size+extra_y))

	def image(self):
		fontPath = self.font if '/' in self.font else fonts_dir+self.font
		try:
			fontPath= fontPath.strip()
			ttf_font = ImageFont.truetype(fontPath, self.size)
		except:
			raise Exception("BAD FONT: "+fontPath)

		padding = self.pos
		text = self.char
		size = ttf_font.getsize(text)
		size = (size[0], size[1] + extra_y)	# add margin
		size = (self.size, self.size)	# ignore rendered font size!
		size = (max_size, max_size + extra_y)	# ignore font size!
		if self.back:
			img = Image.new('RGBA', size, self.back) # background_color
		else:
			img = Image.new('L', size, 'white')	# # grey
		draw = ImageDraw.Draw(img)
		# -
		draw.text((padding['x']-shift_left, padding['y']-shift_up), text, font=ttf_font, fill=self.color)
		if (self.angle>0 or self.angle<0) and self.size>20:
			rot = img.rotate(self.angle, expand=1).resize(size)
			if self.back:
				img = Image.new('RGBA', size, self.back)  # background_color
			else:
				img = Image.new('L', size,'#FFF')#FUCK BUG! 'white')#,'grey')  # # grey
			img.paste(rot, (0, 0), rot)
		return img

	def show(self):
		self.image().show()

	@classmethod
	def random(cls):
		l=letter()
		l.size=pick(sizes)
		l.font=pick(fontnames)
		l.char=pick(letterz)
		l.ord=ord(l.char)
		l.position=(pick(range(0,10)),pick(range(0,10)))
		l.offset=l.position
		l.style=pick(styles) #None #
		l.angle=0

	def __str__(self):
		format="letter{char='%s',size=%d,font='%s',angle=%d,ord=%d,pos=%s}"
		return format % (self.char, self.size, self.font, self.angle, ord(self.char), self.pos)

	def __repr__(self):
		return self.__str__()
	# def print(self):
	# 	print(self.__str__)
	def save(self, path):
		self.image().save(path)


# @classmethod	# can access class cls
# def ls(cls, mypath=None):

# @staticmethod	# CAN'T access class
# def ls(mypath):
import matplotlib.pyplot as plt

def show_matrix(mat):
	plt.matshow(mat, fignum=1)
	# plt.imshow(image)

	# convolve(mat)
	# predict(mat)

	plt.draw()
	plt.waitforbuttonpress()


if __name__ == "__main__":
	while 1:
		# l = letter(char='x')
		l = letter()
		# l.save("letters/letter_%s_%d.png"%(l.char,l.size))
		mat=l.matrix()
		print(np.max(mat))
		print(np.min(mat))
		print(np.average(mat))
		print(l)
		show_matrix(mat)


