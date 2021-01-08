package lothianbus

import (
	"github.com/gofiber/fiber"
    "fmt"
    "io/ioutil"
	"net/http"
	"log"
)

func GetStops(c *fiber.Ctx) {
	lat  := c.Params("lat")

	long := c.Params("long")


	url := fmt.Sprintf("https://tfeapp.com/api/website/nearby_stops.php?latitude=" + lat + "&longitude=" + long)

	response, err := http.Get(url)
    if err != nil {
        fmt.Print(err.Error())
	}
	body, readErr := ioutil.ReadAll(response.Body)
	if readErr != nil {
		log.Fatal(readErr)
	}
	fmt.Println(url)
	c.Send(body)
}

func GetStop(c *fiber.Ctx) {
	stop := c.Params("lat")

	response, err := http.Get("https://tfeapp.com/api/website/stop.php?id=" + stop)
    if err != nil {
        fmt.Print(err.Error())
	}
	body, readErr := ioutil.ReadAll(response.Body)
	if readErr != nil {
		log.Fatal(readErr)
	}
	c.Send(body)
}

func GetBusTimes(c *fiber.Ctx) {
	stop := c.Params("lat")

	response, err := http.Get("https://tfeapp.com/api/website/stop_times.php?stop_id=" + stop)
    if err != nil {
        fmt.Print(err.Error())
	}
	body, readErr := ioutil.ReadAll(response.Body)
	if readErr != nil {
		log.Fatal(readErr)
	}
	c.Send(body)
}

