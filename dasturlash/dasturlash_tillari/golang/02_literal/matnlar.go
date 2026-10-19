package main

import "fmt"

func main() {

	// matn literalini ekranda chop etish
	fmt.Println("Bu matnli qiymat 1 (interpreted string literal)")

	fmt.Println(
		`Bu 
	matnli
		qiymat 2 (raw string literal)`)

	// matn literallarni qo'shish
	fmt.Println("Salom" + "Dunyo!")
}
