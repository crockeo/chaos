package fixtures

import (
	"net/http"
)

const HelloWorldPattern = "/hello_world"

type HelloWorld struct {
}

func NewHelloWorld() *HelloWorld {
	return &HelloWorld{}
}

func (_ *HelloWorld) ServeHTTP(res http.ResponseWriter, req *http.Request) {
	_, err := res.Write([]byte("hello world!"))
	if err != nil {
		res.Write([]byte("failed! :("))
	}
}
