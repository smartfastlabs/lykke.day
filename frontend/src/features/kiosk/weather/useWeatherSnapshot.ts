import { createSignal, onMount } from "solid-js";

import { WEATHER_CODE_LABELS, type WeatherSnapshot } from "../kioskUtils";

export function useWeatherSnapshot() {
  const [weather, setWeather] = createSignal<WeatherSnapshot | null>(null);
  const [weatherError, setWeatherError] = createSignal(false);

  onMount(() => {
    if (!("geolocation" in navigator)) {
      setWeatherError(true);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const url = new window.URL("https://api.open-meteo.com/v1/forecast");
          url.searchParams.set("latitude", latitude.toString());
          url.searchParams.set("longitude", longitude.toString());
          url.searchParams.set("current_weather", "true");
          url.searchParams.set("temperature_unit", "fahrenheit");

          const response = await fetch(url.toString());
          if (!response.ok) {
            setWeatherError(true);
            return;
          }

          const data = (await response.json()) as {
            current_weather?: { temperature: number; weathercode: number };
          };

          if (!data.current_weather) {
            setWeatherError(true);
            return;
          }

          setWeather({
            temperature: Math.round(data.current_weather.temperature),
            condition:
              WEATHER_CODE_LABELS[data.current_weather.weathercode] ??
              "Weather",
          });
        } catch (error) {
          console.error("Weather lookup failed:", error);
          setWeatherError(true);
        }
      },
      () => {
        setWeatherError(true);
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 30 * 60 * 1000 },
    );
  });

  return { weather, weatherError };
}
