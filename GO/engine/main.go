package main

import "fmt"

type gasEngine struct {
	mpg     uint16
	gallons uint16
}

type electricEngine struct {
	mpkwh uint16
	kwh   uint16
}

func (e gasEngine) milesLeft() uint16 {
	return e.gallons * e.mpg
}

func (e electricEngine) milesLeft() uint16 {
	return e.mpkwh * e.kwh
}

type engine interface {
	milesLeft() uint16
}

func can_make_it(e engine, miles uint16) {
	miles_left := e.milesLeft()
	fmt.Printf("%v miles to destination, can run %v miles. ", miles, miles_left)
	if miles <= miles_left {
		fmt.Println("You can make it there!")
	} else {
		fmt.Println("You won't make it there!")
	}
}

func main() {
	var car1 gasEngine = gasEngine{25, 15}
	can_make_it(car1, 50)
	var car2 electricEngine = electricEngine{40, 5}
	can_make_it(car2, 250)
}
