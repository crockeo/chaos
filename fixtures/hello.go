package fixtures

import (
	"context"
	"net/http"
)

func HelloWorld(ctx context.Context, req http.Request) (http.Response, error) {
	return http.Response{}, nil
}
