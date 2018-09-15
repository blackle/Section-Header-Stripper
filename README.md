section-stripper.py is a utility to remove the section header from an ELF file, along with its string table. It also clears the fields in the ELF header related to the section header.

The standard unix utility `strip` doesn't do this, so this is why I created this file.

## Usage:

```bash
./section-stripper.py my-program #strip file in-place
./section-stripper.py my-program my-program-stripped #output stripped file elsewhere (must be chmod'd to be executable)
cat my-program | ./section-stripper > my-program-stripped #do everything with pipes
```
