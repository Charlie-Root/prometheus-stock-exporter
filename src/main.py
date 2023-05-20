import os
import threading
import time
import logging
import yfinance as yf
from prometheus_client import Info, Gauge, generate_latest, CONTENT_TYPE_LATEST
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO)


def get_stock_info(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    return {
        'symbol': symbol,
        'currency': info['currency'],
        'current_price': info['currentPrice'],
        'estimate_high': info['targetHighPrice'],
        'day_high': info['dayHigh'],
        'day_low': info['dayLow'],
        'debt_to_equity': info['debtToEquity'],
        'exchange': info['exchange'],
        'fiftyDayAverage': info['fiftyDayAverage'],
        'fiftyTwoWeekHigh': info['fiftyTwoWeekHigh'],
        'fiftyTwoWeekLow': info['fiftyTwoWeekLow'],
        'fullTimeEmployees': info['fullTimeEmployees'],
        'marketCap': info['marketCap'],
        'recommendationKey': info['recommendationKey'],
        'recommendationMean': info['recommendationMean'],
        'targetHighPrice': info['targetHighPrice'],
        'targetLowPrice': info['targetLowPrice'],
        'targetMeanPrice': info['targetMeanPrice'],
        'targetMedianPrice': info['targetMedianPrice'],
        'twoHundredDayAverage': info['twoHundredDayAverage'],
        'auditRisk': info['auditRisk'],
        'boardRisk': info['boardRisk'],
    }


class StockMetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', CONTENT_TYPE_LATEST)
        self.end_headers()
        self.wfile.write(generate_latest())


def start_prometheus_server():
    server = HTTPServer(('0.0.0.0', 8000), StockMetricsHandler)
    server.serve_forever()


def recommendation_key_to_digit(recommendation_key):
    mapping = {
        'buy': 1,
        'hold': 0,
        'sell': -1,
    }
    return mapping.get(recommendation_key, 0)


def update_stock_metrics():
    stocks = os.getenv('STOCKS', 'AAPL,GOOGL,MSFT,AMZN,PHARM.AS,MT.AS').split(',')

    stock_price_metric = Gauge('stock_price', 'Stock Price', ['stock_symbol'])
    estimate_high_metric = Gauge('estimate_high', 'Estimate High', ['stock_symbol'])
    recommendation_metric = Gauge('recommendation', 'Recommendation', ['stock_symbol'])

    numeric_fields = ['current_price', 'day_high', 'day_low', 'debt_to_equity',
                      'fiftyDayAverage', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow',
                      'fullTimeEmployees', 'marketCap', 'recommendationMean',
                      'targetHighPrice', 'targetLowPrice', 'targetMeanPrice',
                      'targetMedianPrice', 'twoHundredDayAverage', 'auditRisk',
                      'boardRisk']

    field_metrics = {}
    for field in numeric_fields:
        field_metric_name = f'stock_{field}'
        field_metrics[field] = Gauge(field_metric_name, field, ['stock_symbol'])

    while True:
        for symbol in stocks:
            logging.info("Updating metrics for %s", symbol)
            
            stock_info = get_stock_info(symbol)
            stock_price_metric.labels(stock_symbol=symbol).set(stock_info['current_price'])
            estimate_high_metric.labels(stock_symbol=symbol).set(stock_info['estimate_high'])

            # Update additional metrics for numeric fields
            for field, metric in field_metrics.items():
                if field in stock_info:
                    metric.labels(stock_symbol=symbol).set(stock_info[field])

            # Transform recommendationKey field to digit
            recommendation_key = stock_info['recommendationKey']
            digit_recommendation = recommendation_key_to_digit(recommendation_key)
            recommendation_metric.labels(stock_symbol=symbol).set(digit_recommendation)

        time.sleep(10)


if __name__ == '__main__':

    logging.info("Starting Prometheus server...")
    prometheus_thread = threading.Thread(target=start_prometheus_server)
    prometheus_thread.daemon = True
    prometheus_thread.start()
    logging.info("Prometheus server started")

    update_stock_metrics()
