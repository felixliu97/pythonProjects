package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"regexp"
	"sync"
)

var (
	caseInsensitive = flag.Bool("i", false, "Case-insensitive search")
	showLineNumbers = flag.Bool("n", false, "Show line numbers")
	showFilename    = flag.Bool("h", false, "Show filename")
)

func compileRegex(pattern string) (*regexp.Regexp, error) {
	if *caseInsensitive {
		pattern = "(?i)" + pattern
	}
	return regexp.Compile(pattern)
}

func formatLine(line, filename string, lineNum int) string {
	var result string
	if *showFilename && filename != "" {
		result += filename + ":"
	}
	if *showLineNumbers {
		result += fmt.Sprintf("%d:", lineNum)
	}
	return result + line
}

func processInput(input io.Reader, re *regexp.Regexp, filename string) []string {
	scanner := bufio.NewScanner(input)
	var matches []string
	lineNum := 1

	for scanner.Scan() {
		line := scanner.Text()
		if re.MatchString(line) {
			matches = append(matches, formatLine(line, filename, lineNum))
		}
		lineNum++
	}
	return matches
}

func processFile(filename string, re *regexp.Regexp, results chan<- string, wg *sync.WaitGroup) {
	defer wg.Done()

	file, err := os.Open(filename)
	if err != nil {
		results <- fmt.Sprintf("Error opening %s: %v", filename, err)
		return
	}
	defer file.Close()

	matches := processInput(file, re, filename)
	for _, match := range matches {
		results <- match
	}
}

func main() {
	flag.Parse()
	args := flag.Args()
	if len(args) < 1 {
		fmt.Println("Usage: go-grep [flags] pattern [files...]")
		os.Exit(1)
	}

	pattern := args[0]
	re, err := compileRegex(pattern)
	if err != nil {
		log.Fatalf("Invalid regex pattern: %v", err)
	}

	results := make(chan string)
	var wg sync.WaitGroup

	// Handle multiple files or stdin
	if len(args) > 1 {
		*showFilename = true // Auto-enable filename display for multiple files
		for _, filename := range args[1:] {
			wg.Add(1)
			go processFile(filename, re, results, &wg)
		}
	} else {
		// Read from stdin
		wg.Add(1)
		go func() {
			defer wg.Done()
			matches := processInput(os.Stdin, re, "")
			for _, match := range matches {
				results <- match
			}
		}()
	}

	// Close results channel when all processing is done
	go func() {
		wg.Wait()
		close(results)
	}()

	// Print results
	for result := range results {
		fmt.Println(result)
	}
}
