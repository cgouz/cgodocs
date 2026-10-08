// You are given a license key represented as a string s that consists of only alphanumeric characters and dashes. 
// The string is separated into n + 1 groups by n dashes. You are also given an integer k.

// We want to reformat the string s such that each group contains exactly k characters, except for the first group, 
// which could be shorter than k but still must contain at least one character. Furthermore, 
// there must be a dash inserted between two groups, and you should convert all lowercase letters to uppercase.

// Return the reformatted license key.

/*
Example 1:

	Input: s = "5F3Z-2e-9-w", k = 4
	Output: "5F3Z-2E9W"
	Explanation: The string s has been split into two parts, each part has 4 characters.
	Note that the two extra dashes are not needed and can be removed.
*/

package main

import "fmt"

// func licenseKeyFormatting(s string, k int) string {
    
//     var (
//         newS string
//         c int
//     )

//     for i := len(s) -1; i >= 0; i -- {

//     	char := s[i]

//         if char == '-' {
//             continue
//         }

//     	if 'a' <= char && char <= 'z' {
//     		char -= 32
//     	} 

//     	if c < k {

//     		if c == 0 && len(newS) > 0 {
//     			newS = "-" + newS
//     		}

//     		newS = string(char) + newS
//     		c++
//     	}

//     	if c == k {
//     		c = 0
//     	}
//     }

//     return newS
// }

// --------------------2
// func licenseKeyFormatting(s string, k int) string {
// 	result := make([]byte, 0, len(s))

// 	count := 0

// 	for i := len(s) - 1; i >= 0; i-- {
// 		char := s[i]

// 		if char == '-' {
// 			continue
// 		}

// 		if count == k {
// 			result = append(result, '-')
// 			count = 0
// 		}

// 		if char >= 'a' && char <= 'z' {
// 			char -= 'a' - 'A'
// 		}

// 		result = append(result, char)
// 		count++
// 	}

// 	for left, right := 0, len(result)-1; left < right; left, right = left+1, right-1 {
// 		result[left], result[right] = result[right], result[left]
// 	}

// 	return string(result)
// }

//----------------------3
func licenseKeyFormatting(s string, k int) string {
	buf := make([]byte, len(s)+len(s)/k) // upper bound, no counting pass
	j := len(buf)                        // write position (moves left)
	count := 0                           // chars in the current group

	for i := len(s) - 1; i >= 0; i-- {
		c := s[i]
		if c == '-' {
			continue
		}
		if count == k {
			j--
			buf[j] = '-'
			count = 0
		}
		if c >= 'a' && c <= 'z' {
			c -= 'a' - 'A'
		}
		j--
		buf[j] = c
		count++
	}

	return string(buf[j:]) // only the filled tail
}

func main () {

	s, k := "2-5g-3-J", 2

	r := licenseKeyFormatting(s, k)

	fmt.Println(r)
}

