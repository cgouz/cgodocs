package main

import "fmt"

func DecToBin (x int) int {

	var bin int
	var place int = 1

	for x > 0 {

		rem := x % 2
		bin += rem * place
		
		place *= 10
		 
		x /= 2
	}

	return bin
}

func hammingDistance(x int, y int) int {

	var distance int
    
    xBin, yBin := DecToBin(x), DecToBin(y)

    for xBin > 0 || yBin > 0 {

    	if xBin % 2 - yBin % 2 != 0 {
    		distance++ 
    	}

    	xBin /= 10
    	yBin /= 10
    }

    return distance
}

func main () {

	var x, y int = 1577, 1727

	fmt.Println(x^y)

	r := hammingDistance(x, y)

	fmt.Println(r)
	
}