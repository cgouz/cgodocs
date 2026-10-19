package main

import "fmt"
import "reflect"

func main () {
	fmt.Println(reflect.TypeOf(10)) 		// int
	fmt.Println(reflect.TypeOf(1.7)) 		// float64
	fmt.Println(reflect.TypeOf("Salom")) 	// string
	fmt.Println(reflect.TypeOf(`Salom`)) 	// string
	fmt.Println(reflect.TypeOf(true)) 		// bool
	fmt.Println(reflect.TypeOf('A')) 		// int32
}

