// You are given an array of integers nums and an integer target, return indices of the
// two numbers such that they add up to target.
// You may assume that each input would have exactly one solution, and you may not use the same element twice.
// You can return the answer in any order.
/*
Example 1:

Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
*/



package main

import "fmt"

// func twoSum(nums []int, target int) []int {
	
// 	// var numsMap map[int]int =  make(map[int]int)

// 	for i := 0; i < len(nums); i++ {

// 		for j := i + 1; j < len(nums); j++ {

// 			if nums[i] + nums[j] ==  target {

// 				return []int{i, j}
// 			}	
// 		}
// 	}

// 	return nil
// }


func twoSum(nums []int, target int) []int {

	var m map[int]int = make(map[int]int, len(nums))

	for i, num := range nums {

		if _, ok := m[target - num]; !ok {
			m[target - num] = i
		}

		if j, ok := m[num]; ok && i != j {
			return []int{i, j}
		}
	}

	return nil
}

func main () {

	var nums []int = []int{3, 7, 2, 15}
	var target int = 9

	fmt.Println(twoSum(nums, target))
}
