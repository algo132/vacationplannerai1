from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import stripe
from amadeus import Client, ResponseError

app = Flask(__name__, template_folder='../app/templates', static_folder='../app/static')

# Sample data for destinations
destinations = pd.DataFrame({
    'name': ['Paris', 'New York', 'Tokyo', 'Sydney', 'Cape Town']
})

# Stripe API configuration
stripe.api_key = 'sk_live_51N3fmxGVHgwoZ03xacEbfn7pCJmpqVKRyrToryvYkQ93TgZkrl5EIODNqPbCZ00cZfQNS50YIRhx7HzHD'

# Amadeus API configuration
amadeus = Client(
    client_id='1GOy0H21hIN44QDmIMWWO0NARMghRgfm',
    client_secret='T7uLAuCBzOMTcTXi'
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    recommendations = destinations.to_dict(orient='records')
    return jsonify(recommendations)

@app.route('/search_flights', methods=['POST'])
def search_flights():
    data = request.json
    origin = data['origin']
    destination = data['destination']
    departure_date = data['departure_date']
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=1
        )
        return jsonify(response.data)
    except ResponseError as error:
        return jsonify({'error': str(error)})

@app.route('/search_hotels', methods=['POST'])
def search_hotels():
    data = request.json
    city_code = data['city_code']
    check_in_date = data['check_in_date']
    check_out_date = data['check_out_date']
    try:
        response = amadeus.shopping.hotel_offers.get(
            cityCode=city_code,
            checkInDate=check_in_date,
            checkOutDate=check_out_date,
            roomQuantity=1,
            adults=1
        )
        return jsonify(response.data)
    except ResponseError as error:
        return jsonify({'error': str(error)})

@app.route('/book', methods=['POST'])
def book():
    data = request.json
    destination = data['destination']
    base_price = 1000  # Assume a base price for the vacation package
    service_charge = base_price * 0.10
    planning_fee = 100
    total_price = base_price + service_charge + planning_fee

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'Vacation to {destination}',
                },
                'unit_amount': int(total_price * 100),  # Amount in cents
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('success', _external=True),
        cancel_url=url_for('cancel', _external=True),
    )
    return jsonify({'id': session.id})

@app.route('/success')
def success():
    return "Payment successful! Your vacation is booked."

@app.route('/cancel')
def cancel():
    return "Payment canceled."

if __name__ == '__main__':
    app.run(host='0.0.0.0')

