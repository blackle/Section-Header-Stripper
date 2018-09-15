#!/usr/bin/env python3

import sys
from typing import List, Tuple, BinaryIO, cast
from recordclass import recordclass
import struct

def binary_open(filename : str, mode : str) -> BinaryIO:
	return cast(BinaryIO, open(filename, mode + 'b'))

def get_files() -> Tuple[BinaryIO, BinaryIO]:
	inputfile = binary_open("/dev/stdin", 'r')
	outputfile = binary_open("/dev/stdout", 'w')

	argc = len(sys.argv)

	if argc > 1:
		inputfile.close()
		inputfile = binary_open(sys.argv[1], 'r')
	if argc > 2:
		outputfile.close()
		outputfile = binary_open(sys.argv[2], 'w')

	return (inputfile, outputfile)

class BetterStruct:
	def __init__(self, fields : List[Tuple[str, str]], little_endian : bool) -> None:
		struct_fmt = ""
		struct_fields = ""

		if little_endian:
			struct_fmt += "<"
		else:
			struct_fmt += ">"

		for (fmt, name) in fields:
			struct_fmt += fmt + " "
			if not name is None:
				struct_fields += name + " "

		self._struct = struct.Struct(struct_fmt)
		self._tuple = recordclass("my_tuple", struct_fields)
		self.size = self._struct.size

	def read(self, infile : BinaryIO) -> None:
		my_bytes = infile.read(self._struct.size)
		self.fields = self._tuple._make(self._struct.unpack(my_bytes))

	def write(self, outfile : BinaryIO) -> None:
		my_bytes = self._struct.pack(*self.fields)
		outfile.write(my_bytes)

if __name__ == "__main__":
	(inputfile, outputfile) = get_files()

	header_ident = BetterStruct([
		("4s", "magic"),
		("b", "arch"),
		("b", "endianness"),
		("b", "version"),
		("b", "abi"),
		("b", "abi_version"),
		("7x", None),
	], True)

	header_ident.read(inputfile)

	if header_ident.fields.magic != b'\x7FELF':
		print("Input is not an ELF file.", file=sys.stderr)
		exit(1)

	if header_ident.fields.arch != 2:
		print("Only 64-bit ELF files are currently supported.", file=sys.stderr)
		exit(1)

	header = BetterStruct([
		("H", "type"),
		("H", "machine"),
		("L", "version"),
		("Q", "entry"),
		("Q", "phoff"),
		("Q", "shoff"),
		("L", "flags"),
		("H", "ehsize"),
		("H", "phentsize"),
		("H", "phnum"),
		("H", "shentsize"),
		("H", "shnum"),
		("H", "shstrndx"),
	], header_ident.fields.endianness == 1)

	header.read(inputfile)

	shoff = header.fields.shoff
	shentsize = header.fields.shentsize
	shnum = header.fields.shnum
	shstrndx = header.fields.shstrndx

	header.fields.shoff = 0
	header.fields.shentsize = 0
	header.fields.shnum = 0
	header.fields.shstrndx = 0

	shsize = shentsize*shnum

	offset = shoff - (header_ident.size + header.size)

	intermediate_bytes = inputfile.read(offset)
	sh_bytes = inputfile.read(shsize)
	leftover_bytes = inputfile.read(-1)

	print(shstrndx, file=sys.stderr)

	if len(leftover_bytes) != 0:
		sh_bytes = b'\x00' * len(sh_bytes)
	else:
		sh_bytes = b''

	header_ident.write(outputfile)
	header.write(outputfile)
	outputfile.write(intermediate_bytes)
	outputfile.write(sh_bytes)
	outputfile.write(leftover_bytes)

	inputfile.close()
	outputfile.close()