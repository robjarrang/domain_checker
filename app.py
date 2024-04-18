import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import flask
import json
import dns.resolver

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

def load_domains():
    with open('domains.json', 'r') as file:
        return json.load(file)

def check_dns_record(domain, record_type, selector=None):
    if record_type == "DKIM":
        domain = f"{selector}._domainkey.{domain}"
    elif record_type == "DMARC":
        domain = f"_dmarc.{domain}"
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        if answers:
            return "Found", "success", ', '.join([str(rdata) for rdata in answers])
        else:
            return "Not Found", "warning", "No records found"
    except dns.resolver.NoAnswer:
        return "Not Found", "warning", "No records found"
    except Exception as e:
        return "Error", "danger", str(e)

domains = load_domains()

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Domain DNS Checker"), width=12, className="mb-3")),
    dbc.Row(dbc.Col(dbc.Button("Check Domains", id="check-button", color="primary", className="me-2"))),
    dbc.Row(dbc.Col(html.Div(id="output-container"), width=12))
], fluid=True)

@app.callback(
    Output('output-container', 'children'),
    [Input('check-button', 'n_clicks')]
)
def update_output(n_clicks):
    if n_clicks is None:
        return dbc.Alert("Click the button to start checking domains.", color="info")
    elif n_clicks > 0:
        children = []
        for domain, info in domains.items():
            spf_result, spf_status, spf_details = check_dns_record(domain, 'SPF')
            dkim_result, dkim_status, dkim_details = check_dns_record(domain, 'DKIM', info['selector'])
            dmarc_result, dmarc_status, dmarc_details = check_dns_record(domain, 'DMARC')
            domain_results = dbc.Card([
                dbc.CardHeader(html.H3(domain)),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(html.P([html.Strong("SPF: "), dbc.Badge(spf_result, color=spf_status)])),
                        dbc.Col(dbc.Button("Details", id=f"toggle-spf-{domain}", color="link")),
                        dbc.Collapse(dbc.CardText(spf_details), id=f"collapse-spf-{domain}")
                    ]),
                    dbc.Row([
                        dbc.Col(html.P([html.Strong("DKIM: "), dbc.Badge(dkim_result, color=dkim_status)])),
                        dbc.Col(dbc.Button("Details", id=f"toggle-dkim-{domain}", color="link")),
                        dbc.Collapse(dbc.CardText(dkim_details), id=f"collapse-dkim-{domain}")
                    ]),
                    dbc.Row([
                        dbc.Col(html.P([html.Strong("DMARC: "), dbc.Badge(dmarc_result, color=dmarc_status)])),
                        dbc.Col(dbc.Button("Details", id=f"toggle-dmarc-{domain}", color="link")),
                        dbc.Collapse(dbc.CardText(dmarc_details), id=f"collapse-dmarc-{domain}")
                    ])
                ])
            ])
            children.append(domain_results)
        return children
    return dbc.Alert("Click the button to check domains.", color="warning")

# Add callbacks for toggling the visibility of each detail section
for domain in domains.keys():
    @app.callback(
        Output(f"collapse-spf-{domain}", 'is_open'),
        [Input(f"toggle-spf-{domain}", 'n_clicks')],
        [State(f"collapse-spf-{domain}", 'is_open')],
        prevent_initial_call=True
    )
    def toggle_spf(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output(f"collapse-dkim-{domain}", 'is_open'),
        [Input(f"toggle-dkim-{domain}", 'n_clicks')],
        [State(f"collapse-dkim-{domain}", 'is_open')],
        prevent_initial_call=True
    )
    def toggle_dkim(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output(f"collapse-dmarc-{domain}", 'is_open'),
        [Input(f"toggle-dmarc-{domain}", 'n_clicks')],
        [State(f"collapse-dmarc-{domain}", 'is_open')],
        prevent_initial_call=True
    )
    def toggle_dmarc(n, is_open):
        if n:
            return not is_open
        return is_open

if __name__ == '__main__':
    app.run_server(debug=True)
