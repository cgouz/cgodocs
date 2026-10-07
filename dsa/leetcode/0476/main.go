// The complement of an integer is the integer you get when you flip all the 0's to 1's and all the 1's to 0's in its binary representation.

// For example, The integer 5 is "101" in binary and its complement is "010" which is the integer 2.
// Given an integer num, return its complement.

 
/*
Example 1:

	Input: num = 5
	Output: 2
	Explanation: The binary representation of 5 is 101 (no leading zero bits), and its complement is 010. So you need to output 2.
	Example 2:

	Input: num = 1
	Output: 0
	Explanation: The binary representation of 1 is 1 (no leading zero bits), and its complement is 0. So you need to output 0.
*/

package main

import "fmt"

func DecToReBin(x int) string {
	if x == 0 {
		return "1"
	}

	bin := ""

	for x > 0 {
		remainder := x % 2

		if remainder == 1 {
			bin = "0" + bin
		} else {
			bin = "1" + bin
		}

		x /= 2
	}

	return bin
}

func BinToDec(bin string) int {
	dec := 0

	for _, bit := range bin {
		dec *= 2

		if bit == '1' {
			dec++
		}
	}

	return dec
}

func findComplement(num int) int {
	return BinToDec(DecToReBin(num))
}
func main () {

	var x int = 20161211

	fmt.Println(findComplement(x))

}