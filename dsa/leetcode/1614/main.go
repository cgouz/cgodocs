// Given a valid parentheses string s, return the nesting depth of s. The nesting depth is the maximum number of nested parentheses.

/*
Example 1:
	Input: s = "(1+(2*3)+((8)/4))+1"
	
	Output: 3
	
	Explanation:
	
	Digit 8 is inside of 3 nested parentheses in the string.	
*/

package main

import "fmt"

func maxDepth(s string) int {
    
    var count, max int

    for _, ch := range s {

    	if ch == '(' {
    		count ++
    	} 

    	if count > max {
    		max = count
    	}

    	if ch == ')' {
    		count --
    	}
    }

   return max
}

func main () {

	fmt.Println(maxDepth("()(())((()()))"))
}