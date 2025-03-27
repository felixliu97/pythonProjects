package main

import "fmt"

func main() {
	// Boolean
	var isTrue bool = true
	fmt.Println("Boolean:", isTrue)

	// Integer
	var num int = 42
	fmt.Println("Integer:", num)

	// Float
	var pi float64 = 3.14
	fmt.Println("Float:", pi)

	// String
	var message string = "Hello, Go!"
	fmt.Println("String:", message)

	// Array
	var arr [3]int = [3]int{1, 2, 3}
	fmt.Println("Array:", arr)

	arr2 := [...]int32{1, 2, 3, 4, 5}
	fmt.Println("Array2:", arr2)

	// Slice
	var slice []int = []int{1, 2, 3}
	fmt.Println("Slice:", slice)
	slice = append(slice, 5)
	fmt.Println("Slice:", slice)

	//Rune
	// var my_str = "Résumés"
	var my_str = []rune("Résumés")
	var indexed = my_str[1]
	fmt.Printf("Rune: %v, %T\n", indexed, indexed)
	for i, v := range my_str {
		fmt.Println(i, v)
	}

	// Map
	var m map[string]int = map[string]int{"one": 1, "two": 2}
	fmt.Println("Map:", m)

	// Struct
	type Person struct {
		Name string
		Age  int
	}
	var p Person = Person{"Alice", 30}
	fmt.Println("Struct:", p)

	// Pointer
	var ptr *int = &num
	fmt.Println("Pointer:", *ptr)

	// Function
	add := func(a int, b int) int {
		return a + b
	}
	fmt.Println("Function:", add(2, 3))

	// Interface
	var i interface{} = "Hello, Interface!"
	fmt.Println("Interface:", i)

	// Channel
	ch := make(chan int)
	go func() { ch <- 42 }()
	fmt.Println("Channel:", <-ch)
}
