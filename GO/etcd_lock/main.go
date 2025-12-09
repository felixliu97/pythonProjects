package main

import (
	"context"
	"flag"
	"log"
	"time"

	clientv3 "go.etcd.io/etcd/client/v3"
	"go.etcd.io/etcd/client/v3/concurrency"
)

func main() {
	var name = flag.String("name", "worker", "name of the worker")
	var ttl = flag.Int("ttl", 5, "ttl for the session")
	var endpoint = flag.String("endpoint", "localhost:2379", "etcd endpoint")
	flag.Parse()

	log.Println("Worker starting...")

	// 1. Connect to etcd
	log.Printf("[%s] Connecting to etcd at %s with %ds timeout...", *name, *endpoint, 5)
	cli, err := clientv3.New(clientv3.Config{
		Endpoints:   []string{*endpoint},
		DialTimeout: 5 * time.Second,
	})
	if err != nil {
		log.Fatal(err)
	}
	defer cli.Close()

	// 2. Create a session (leases logic)
	// This automatically keeps the lease alive.
	s, err := concurrency.NewSession(cli, concurrency.WithTTL(*ttl))
	if err != nil {
		log.Fatal(err)
	}
	defer s.Close()

	// 3. Create a mutex on a shared key
	m := concurrency.NewMutex(s, "/my-distributed-lock")

	log.Printf("[%s] trying to acquire lock", *name)
	ctx := context.Background()

	// 4. Acquire lock (blocking)
	if err := m.Lock(ctx); err != nil {
		log.Fatal(err)
	}
	log.Printf("[%s] ACQUIRED lock", *name)

	// 5. Critical section (simulate work)
	workDuration := 5 * time.Second
	log.Printf("[%s] doing work for %v...", *name, workDuration)
	time.Sleep(workDuration)

	// 6. Release lock
	if err := m.Unlock(ctx); err != nil {
		log.Fatal(err)
	}
	log.Printf("[%s] RELEASED lock", *name)
}
