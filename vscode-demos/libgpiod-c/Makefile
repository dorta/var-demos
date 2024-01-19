# Remove D_FORTIFY_SOURCE since it can't be used with -O0
CC:=$(filter-out -D_FORTIFY_SOURCE=2,$(CC))

all: main.c
	$(CC) $(CFLAGS) -O0 -lgpiod main.c -g -o hello.bin
clean:
	rm -f hello.bin
