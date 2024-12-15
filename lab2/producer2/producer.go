package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"time"
)

func sendMessagesToBroker(pdType, matrixSize int) {
	brokerURL := "http://nginx:80/data"
    endURL := "http://nginx:80/end"

	for i := 0; i < matrixSize*matrixSize; i++ {
		if i%1000 == 0 {
			fmt.Printf("Sending message %d...\n", i)
		}

		data := map[string]interface{}{
			"message_type":    pdType,
			"message_content": rand.Intn(1000) + 1,
		}

		jsonData, err := json.Marshal(data)
		if err != nil {
			fmt.Printf("Error encoding JSON: %v\n", err)
			continue
		}

		if err := sendPostRequest(brokerURL, jsonData); err != nil {
			time.Sleep(1 * time.Second)
			continue
		}
	}

	endData := map[string]interface{}{
		"message_type":    pdType,
		"message_content": -1,
	}

	endJsonData, err := json.Marshal(endData)
	if err != nil {
		fmt.Printf("Error encoding JSON: %v\n", err)
		return
	}

	if err := sendPostRequest(endURL, endJsonData); err != nil {
		fmt.Printf("Error sending end message: %v\n", err)
	}
}

func sendPostRequest(url string, jsonData []byte) error {
	response, err := http.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("Error sending message: %v", err)
	}
	defer response.Body.Close()

	if response.StatusCode == http.StatusBadRequest {
		return fmt.Errorf("Received error status: %v", response.StatusCode)
	}

	return nil
}

func main() {
	if len(os.Args) > 2 {
		arg1, err := strconv.Atoi(os.Args[1])
		if err != nil {
			fmt.Println("Invalid producer type. Should be 1 or 2")
			return
		}

		arg2, err := strconv.Atoi(os.Args[2])
		if err != nil {
			fmt.Println("Invalid matrix size argument. Should be an integer")
			return
		}

		sendMessagesToBroker(arg1, arg2)
	} else {
		fmt.Println("Usage: <program> <producer type: 1 or 2> <number of messages to send>")
	}
}