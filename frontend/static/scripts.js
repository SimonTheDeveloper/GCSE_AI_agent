let selectedSortOrder = 'Top flights'; // Default sort order
let selectedAirlines = []; // Default to an empty array for airlines
let selectedStops = 'Any number of stops'; // Default to any number of stops

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded event fired');
    fetchFlights();

    // Set up event listeners for airline checkboxes
    document.querySelectorAll('.airline-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (event) => {
            updateAirlines(event.target.value);
        });
    });

    // Set up event listeners for sort order selection
    document.querySelectorAll('.sort-order-radio').forEach(radio => {
        radio.addEventListener('change', (event) => {
            updateSortOrder(event.target.value);
        });
    });

    // Set up event listeners for stops selection
    document.querySelectorAll('.stops-radio').forEach(radio => {
        radio.addEventListener('change', (event) => {
            updateStops(event.target.value);
        });
    });
});

function formatDateTime(dateTime) {
    const date = new Date(dateTime);
    const hours = date.getHours();
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

function formatNumberOfStops(numberOfStops) {
    if (numberOfStops === 0) {
        return 'Non-stop';
    }
    if (numberOfStops === 1) {
        return '1 stop';
    }
    return `${numberOfStops} stops`;
}

function formatArrivalTime(departureDateTime, arrivalDateTime) {
    const departureDate = new Date(departureDateTime);
    const arrivalDate = new Date(arrivalDateTime);
    const nextDay = arrivalDate.getDate() > departureDate.getDate() ? `<sup>+1</sup>` : '';
    return `${formatDateTime(arrivalDateTime)}${nextDay}`;
}

function calculateFlightDuration(departureDateTime, arrivalDateTime) {
    const departureDate = new Date(departureDateTime);
    const arrivalDate = new Date(arrivalDateTime);
    const durationMs = arrivalDate - departureDate;
    const durationHours = Math.floor(durationMs / (1000 * 60 * 60));
    const durationMinutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    return `${durationHours} hr ${durationMinutes} min`;
}

function formatPrice(price) {
    return price.toFixed(2);
}

async function fetchConfig() {
    try {
        console.log('Fetching configuration...');
        const response = await fetch('/frontend/static/config.json');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const config = await response.json();
        console.log('Configuration fetched successfully:', config);
        return config;
    } catch (error) {
        console.error('Failed to fetch config:', error);
        return null;
    }
}

function updateSortOrder(sortOrder) {
    selectedSortOrder = sortOrder;
    fetchFlights();
}

function updateAirlines(airline) {
    if (!selectedAirlines.includes(airline)) {
        selectedAirlines.push(airline);
    } else {
        selectedAirlines = selectedAirlines.filter(a => a !== airline);
    }
    fetchFlights();
}

function updateStops(stops) {
    selectedStops = stops;
    fetchFlights();
}

async function fetchFlights() {
    console.log('Fetching flights...Selected sort order:', selectedSortOrder, 'Selected airlines:', Array.from(selectedAirlines), 'Selected stops:', selectedStops);
    const config = await fetchConfig();
    if (!config) {
        console.error('No configuration available. Aborting fetchFlights.');
        return;
    }

    try {
        const response = await fetch(config.webAddresses.flightsApi);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        let flights = await response.json();

        console.log('Flights fetched successfully:', flights);

        // Filter flights based on the selected airlines
        if (selectedAirlines.length > 0) {
            flights = flights.filter(flight =>
                selectedAirlines.some(airline =>
                    airline.toLowerCase() === flight.airline.toLowerCase()));
        }

        // Filter flights based on the selected stops
        if (selectedStops !== 'Any number of stops') {
            flights = flights.filter(flight => {
                switch (selectedStops) {
                    case 'Non-stop only':
                        return flight.number_of_stops === 0;
                    case 'One stop or fewer':
                        return flight.number_of_stops <= 1;
                    case 'Two stops or fewer':
                        return flight.number_of_stops <= 2;
                    default:
                        return true;
                }
            });
        }

        // Sort flights based on the selected sort order
        flights = sortFlights(flights, selectedSortOrder);

        displayFlights(flights);
    } catch (error) {
        console.error('Failed to fetch flights:', error);
    }
}

function displayFlights(flights) {
    const flightListDiv = document.getElementById('flight-list');
    const moreFlightsDiv = document.getElementById('more-flights');
    const flightTemplate = document.getElementById('flight-template').innerHTML;

    // Clear previous content
    flightListDiv.innerHTML = '';
    moreFlightsDiv.innerHTML = '';

    // Display the first five flights
    flights.slice(0, 5).forEach(flight => {
        const flightHTML = flightTemplate
            .replace('{{flight_id}}', flight.flight_id)
            .replace('{{source}}', flight.source)
            .replace('{{sink}}', flight.sink)
            .replace('{{airline}}', flight.airline)
            .replace('{{departure_dt}}', formatDateTime(flight.departure_dt))
            .replace('{{arrival_dt}}', formatArrivalTime(flight.departure_dt, flight.arrival_dt))
            .replace('{{flight_duration}}', calculateFlightDuration(flight.departure_dt, flight.arrival_dt))
            .replace('{{number_of_stops}}', formatNumberOfStops(flight.number_of_stops))
            .replace('{{emissions}}', flight.emissions)
            .replace('{{price}}', formatPrice(flight.price))
            .replace('{{airline_logo}}', getAirlineLogo(flight.airline));

        flightListDiv.insertAdjacentHTML('beforeend', flightHTML);
    });

    // Display the remaining flights
    flights.slice(5).forEach(flight => {
        const flightHTML = flightTemplate
            .replace('{{flight_id}}', flight.flight_id)
            .replace('{{source}}', flight.source)
            .replace('{{sink}}', flight.sink)
            .replace('{{airline}}', flight.airline)
            .replace('{{departure_dt}}', formatDateTime(flight.departure_dt))
            .replace('{{arrival_dt}}', formatArrivalTime(flight.departure_dt, flight.arrival_dt))
            .replace('{{flight_duration}}', calculateFlightDuration(flight.departure_dt, flight.arrival_dt))
            .replace('{{number_of_stops}}', formatNumberOfStops(flight.number_of_stops))
            .replace('{{emissions}}', flight.emissions)
            .replace('{{price}}', formatPrice(flight.price))
            .replace('{{airline_logo}}', getAirlineLogo(flight.airline));

        moreFlightsDiv.insertAdjacentHTML('beforeend', flightHTML);
    });
}

function sortFlights(flights, sortOrder) {
    switch (sortOrder) {
        case 'Price':
            return flights.sort((a, b) => a.price - b.price);
        case 'Departure Time':
            return flights.sort((a, b) => new Date(a.departure_dt) - new Date(b.departure_dt));
        case 'Arrival Time':
            return flights.sort((a, b) => new Date(a.arrival_dt) - new Date(b.arrival_dt));
        case 'Duration':
            return flights.sort((a, b) => {
                const durationA = new Date(a.arrival_dt) - new Date(a.departure_dt);
                const durationB = new Date(b.arrival_dt) - new Date(b.departure_dt);
                return durationA - durationB;
            });
        case 'Emissions':
            return flights.sort((a, b) => a.emissions - b.emissions);
        default:
            return flights;
    }
}

function getAirlineLogo(airline) {
    const logos = {
        'EASYJET': '/frontend/static/icons/easyjet.png',
        'British Airways': '/frontend/static/icons/british_airways.png',
        'WIZZ AIR': '/frontend/static/icons/wizzair.png',
        'KLM': '/frontend/static/icons/klm.png'
    };
    return logos[airline] || '/frontend/static/icons/default.png';
}