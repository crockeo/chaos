package fixtures

import (
	"net/http"

	cowsay "github.com/Code-Hex/Neo-cowsay/v2"
)

const HelloWorldPattern = "/hello_world"

type HelloWorld struct {
}

func NewHelloWorld() *HelloWorld {
	return &HelloWorld{}
}

func (_ *HelloWorld) ServeHTTP(res http.ResponseWriter, req *http.Request) {
	message, err := cowsay.Say(
		"Hello World",
	)
	if err != nil {
		panic(err)
	}

	_, err = res.Write([]byte(message))
	if err != nil {
		panic(err)
	}
}
