import dash
from dash import html, dcc, callback_context
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import flask
import json
import dns.resolver
import pandas as pd
from io import StringIO

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

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
        return True, ', '.join([str(rdata) for rdata in answers])
    except Exception as e:
        return False, str(e)

domains = load_domains()

app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(html.H1("Domain DNS Checker",
                        className='text-center text-primary mb-4'),
                width=12)
    ),
    dbc.Row([
        dbc.Col([
            html.H5("Select Record Types", className="mb-3"),
            dcc.Checklist(
                id='record-type-checklist',
                options=[
                    {'label': 'SPF', 'value': 'spf'},
                    {'label': 'DKIM', 'value': 'dkim'},  
                    {'label': 'DMARC', 'value': 'dmarc'}
                ],
                value=['spf', 'dkim', 'dmarc'], 
                labelStyle={'display': 'inline-block', 'cursor': 'pointer', 'margin-right':'20px'}
            ),
            html.Div([
                html.H5("Additional Domains", className="mt-4 mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Input(id='additional-domain-input', placeholder='Enter domain', type='text')
                    ], width=6),
                    dbc.Col([
                        dbc.Input(id='additional-selector-input', placeholder='Enter DKIM selector', type='text')
                    ], width=6)
                ]),
                dbc.Button("Add Domain", id="add-domain-button", color="secondary", className="mt-2")
            ], className="mt-4"),
            html.Div(id='additional-domains-container', className='mt-3')
        ], width=4),
        dbc.Col([
            dbc.Button("Check Domains", color="primary", id="check-button"),
            dbc.Spinner(html.Div(id="loading-output"), color="primary"),
            html.Div([
                dbc.Button("Export Results", color="secondary", id="export-button", className="mt-3"),
                dcc.Download(id="download-dataframe-csv")
            ])
        ], width=8)
    ], className="mb-5"), 
    dbc.Spinner(html.Div(id="loading-output"), color="primary", fullscreen=True, fullscreen_style={"opacity": "0.8", "background-color": "rgba(255, 255, 255, 0.8)"}),
    html.Div(id='output-container', className='row')
], fluid=True)

@app.callback(
    Output('additional-domains-container', 'children'),
    Input('add-domain-button', 'n_clicks'),
    State('additional-domain-input', 'value'),
    State('additional-selector-input', 'value'),
    State('additional-domains-container', 'children'),
    prevent_initial_call=True
)
def add_additional_domain(n_clicks, domain, selector, current_domains):
    if n_clicks and domain:
        new_domain = html.Div([
            html.P(f"Domain: {domain}, Selector: {selector}"),
            dcc.Input(id={'type': 'additional-domain', 'index': n_clicks}, value=domain, type='hidden'),
            dcc.Input(id={'type': 'additional-selector', 'index': n_clicks}, value=selector, type='hidden')
        ])
        current_domains.append(new_domain)
    return current_domains

@app.callback(
    Output('output-container', 'children'),
    Output('download-dataframe-csv', 'data'),
    Output('loading-output', 'children'),
    Input('check-button', 'n_clicks'),
    Input('export-button', 'n_clicks'),
    State('record-type-checklist', 'value'),
    State({'type': 'additional-domain', 'index': ALL}, 'value'),
    State({'type': 'additional-selector', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def update_output(check_clicks, export_clicks, selected_record_types, additional_domains, additional_selectors):
    ctx = callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'check-button':
        all_domains = {**domains}
        if additional_domains:
            all_domains.update({domain: {'selector': selector} for domain, selector in zip(additional_domains, additional_selectors)})

        results = []
        output_divs = []
        for domain, info in all_domains.items():
            domain_results = {'Domain': domain}
            domain_div = dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.H4(domain, className="card-title")),
                    dbc.CardBody([
                        html.Div([
                            dbc.Button(
                                f"{record_type.upper()}: {'Found' if found else 'Not Found'}",
                                id={'type': f'toggle-{record_type}', 'index': domain},
                                color="success" if found else "danger",
                                className="mb-3",
                                n_clicks=0
                            ),
                            dbc.Collapse(
                                dbc.Card(dbc.CardBody(result)),
                                id={'type': f'collapse-{record_type}', 'index': domain},
                                is_open=False
                            )
                        ]) for record_type, (found, result) in [
                            (record_type, check_dns_record(domain, record_type.upper(), info['selector']) if record_type == 'dkim' else check_dns_record(domain, record_type.upper()))
                            for record_type in selected_record_types
                        ]
                    ])
                ]), width=4, className="mb-4"
            )
            output_divs.append(domain_div)

            for record_type in selected_record_types:
                if record_type == 'dkim':
                    found, result = check_dns_record(domain, record_type.upper(), info['selector'])
                else:
                    found, result = check_dns_record(domain, record_type.upper())
                domain_results[record_type.upper()] = 'Found' if found else 'Not Found'
                domain_results[f'{record_type.upper()} Result'] = result
            results.append(domain_results)

        df = pd.DataFrame(results)

        return output_divs, None, None

    elif button_id == 'export-button':
        if results:
            return None, dcc.send_data_frame(df.to_csv, "domain_results.csv"), None
        else:
            return None, None, None

    return None, None, "Checking DNS records..."

@app.callback(
    Output({'type': 'collapse-spf', 'index': MATCH}, 'is_open'),
    Input({'type': 'toggle-spf', 'index': MATCH}, 'n_clicks'),
    State({'type': 'collapse-spf', 'index': MATCH}, 'is_open'),
)
def toggle_spf_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output({'type': 'collapse-dkim', 'index': MATCH}, 'is_open'),
    Input({'type': 'toggle-dkim', 'index': MATCH}, 'n_clicks'),
    State({'type': 'collapse-dkim', 'index': MATCH}, 'is_open'),
)
def toggle_dkim_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output({'type': 'collapse-dmarc', 'index': MATCH}, 'is_open'),
    Input({'type': 'toggle-dmarc', 'index': MATCH}, 'n_clicks'),
    State({'type': 'collapse-dmarc', 'index': MATCH}, 'is_open'),
)
def toggle_dmarc_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

if __name__ == '__main__':
    app.run_server(debug=True)