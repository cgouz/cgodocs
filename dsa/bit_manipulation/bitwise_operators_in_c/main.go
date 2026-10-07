package main

import (
	"fmt"
	"time"
)

func hammingBitwise(x, y int) int {

	n := x ^ y
	distance := 0

	for n > 0 {
		distance += n & 1
		n >>= 1
	}

	return distance
}

func hammingWithoutBitwise(x, y int) int {
	distance := 0

	for x > 0 || y > 0 {
		if x%2 != y%2 {
			distance++
		}

		x /= 2
		y /= 2
	}

	return distance
}

func main() {
	const count = 100_000_000

	start := time.Now()

	for i := 0; i < count; i++ {
		hammingBitwise(9223372036854775807, 1)
	}

	fmt.Println("Bitwise:", time.Since(start))

	start = time.Now()

	for i := 0; i < count; i++ {
		hammingWithoutBitwise(9223372036854775807, 1)
	}

	fmt.Println("Without bitwise:", time.Since(start))
}
