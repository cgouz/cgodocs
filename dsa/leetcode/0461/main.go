// You are given row x col grid representing a map where grid[i][j] = 1 represents land and grid[i][j] = 0 represents water.
//
// Grid cells are connected horizontally/vertically (not diagonally). The grid is completely surrounded by water, 
// and there is exactly one island (i.e., one or more connected land cells).
//
// The island doesn't have "lakes", meaning the water inside isn't connected to the water around the island. 
// One cell is a square with side length 1. The grid is rectangular, width and height don't exceed 100. Determine the perimeter of the island.

/*
Input: 

	grid = [
			[0,1,0,0],
			[1,1,1,0],
			[0,1,0,0],
			[1,1,0,0]
		]
Output: 16
Explanation: The perimeter is the 16 yellow stripes in the image above.
*/
package main

func islandPerimeter(grid [][]int) int {

	perimeter := 0

	rows := len(grid)
	cols := len(grid[0])

	for i := 0; i < rows; i++ {
		for j := 0; j < cols; j++ {

			if grid[i][j] == 0 {
				continue
			}

			// Every land cell initially has 4 sides
			perimeter += 4

			// Check top neighbor
			if i > 0 && grid[i-1][j] == 1 {
				perimeter -= 2
			}

			// Check left neighbor
			if j > 0 && grid[i][j-1] == 1 {
				perimeter -= 2
			}
		}
	}

	return perimeter
}

// func islandPerimeter(grid [][]int) int {
// 	rows := len(grid)
// 	cols := len(grid[0])
// 	perimeter := 0

// 	for r := 0; r < rows; r++ {
// 		for c := 0; c < cols; c++ {
// 			if grid[r][c] == 1 {
// 				perimeter += 4

// 				// Nếu ô phía trên là đất liền -> trừ 2 cạnh chung
// 				if r > 0 && grid[r-1][c] == 1 {
// 					perimeter -= 2
// 				}
// 				// Nếu ô bên trái là đất liền -> trừ 2 cạnh chung
// 				if c > 0 && grid[r][c-1] == 1 {
// 					perimeter -= 2
// 				}
// 			}
// 		}
// 	}

// 	return perimeter
// }

func main () {

}