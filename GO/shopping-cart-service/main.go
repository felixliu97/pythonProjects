package main

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

// CartItem 表示购物车中的一个商品
type CartItem struct {
	ProductID int `json:"product_id"`
	Quantity  int `json:"quantity"`
}

// ShoppingCart 使用 map 来存储购物车内容，key 是 ProductID
type ShoppingCart struct {
	Items map[int]CartItem `json:"items"`
}

// 模拟的商品数据 (实际应用中可能从数据库获取)
var products = map[int]string{
	1: "Laptop",
	2: "Mouse",
	3: "Keyboard",
}

// 模拟的购物车数据 (在实际应用中，每个用户应该有自己的购物车)
var cart = ShoppingCart{
	Items: make(map[int]CartItem),
}

// addToCartHandler 处理添加商品到购物车的请求
func addToCartHandler(c *gin.Context) {
	var newItem CartItem
	if err := c.BindJSON(&newItem); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	if _, ok := products[newItem.ProductID]; !ok {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Product not found"})
		return
	}

	if item, ok := cart.Items[newItem.ProductID]; ok {
		item.Quantity += newItem.Quantity
		cart.Items[newItem.ProductID] = item
	} else {
		cart.Items[newItem.ProductID] = newItem
	}
	c.JSON(http.StatusOK, gin.H{"message": "Product added to cart"})
}

// viewCartHandler 处理查看购物车内容的请求
func viewCartHandler(c *gin.Context) {
	cartDetails := make(map[string]int)
	for productID, item := range cart.Items {
		if productName, ok := products[productID]; ok {
			cartDetails[productName] = item.Quantity
		}
	}
	c.JSON(http.StatusOK, gin.H{"items": cartDetails})
}

// removeFromCartHandler 处理从购物车移除商品的请求
func removeFromCartHandler(c *gin.Context) {
	productIDStr := c.Param("product_id")
	productID, err := strconv.Atoi(productIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid product ID"})
		return
	}

	if _, ok := cart.Items[productID]; !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "Product not in cart"})
		return
	}

	delete(cart.Items, productID)
	c.JSON(http.StatusOK, gin.H{"message": "Product removed from cart"})
}

func main() {
	r := gin.Default()

	r.POST("/cart/add", addToCartHandler)
	r.GET("/cart", viewCartHandler)
	r.DELETE("/cart/remove/:product_id", removeFromCartHandler)

	r.Run(":8080")
}
