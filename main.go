package main

import (
	"github.com/gofiber/fiber"
	"github.com/stuartgraham/LothianBusGo/lothianbus"
)

func setupRoutes(app *fiber.App) {
	app.Get("/api/v1/getstops/:lat/:long", lothianbus.GetStops)
	app.Get("/api/v1/getstop/:stop", lothianbus.GetStop)
	app.Get("/api/v1/getbustimes/:stop", lothianbus.GetBusTimes)
	app.Static("/", "./public/")

}

func main () {
	app := fiber.New()
	setupRoutes(app)
	app.Listen(80)
}
