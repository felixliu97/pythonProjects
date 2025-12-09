package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"
)

// Response standardizes the JSON response format
type Response struct {
	Message string `json:"message"`
	Path    string `json:"path,omitempty"`
	Status  string `json:"status,omitempty"`
}

// loggingMiddleware wraps an http.Handler to log request details
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Wrap ResponseWriter to capture status code if needed,
		// but for simplicity we'll log the request receipt.
		log.Printf("[INFO] Started %s %s", r.Method, r.URL.Path)

		next.ServeHTTP(w, r)

		log.Printf("[INFO] Completed %s %s in %v", r.Method, r.URL.Path, time.Since(start))
	})
}

// respondJSON helper to write JSON responses
func respondJSON(w http.ResponseWriter, status int, payload interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		log.Printf("[ERROR] Failed to encode response: %v", err)
	}
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	resp := Response{
		Message: "Hi there, request received!",
		Path:    r.URL.Path,
	}
	respondJSON(w, http.StatusOK, resp)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	respondJSON(w, http.StatusOK, Response{
		Status:  "up",
		Message: "Service is healthy",
	})
}

func main() {
	// Configuration via environment variables
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	// Router setup
	mux := http.NewServeMux()
	mux.HandleFunc("/", rootHandler)
	mux.HandleFunc("/health", healthHandler)

	// Wrap mux with middleware
	handler := loggingMiddleware(mux)

	// Server setup
	srv := &http.Server{
		Addr:         ":" + port,
		Handler:      handler,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	log.Printf("[INFO] Server is starting on port %s...", port)
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("[FATAL] Server failed: %v", err)
	}
}
