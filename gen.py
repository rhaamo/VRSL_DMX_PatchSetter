#!/usr/bin/env python
import sys
import os
import argparse
import yaml
import jinja2
import datetime
import json

# Thoses are VRSL values
MAX_DMX_UNIVERSES = 9 + 1
MAX_DMX_CHANNELS = 512 + 1

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("vrsl_json", help="VRSL Json file", type=str)
arg_parser.add_argument("extras", help="Extra fixtures and venue infos", type=str)
arg_parser.add_argument("outfile", help="Output file", type=str)
arg_parser.add_argument("--pdf", help="Output in PDF", action="store_true")
arg_parser.add_argument("--html", help="Output in HTML", action="store_true")
args = arg_parser.parse_args()

if (not args.pdf and not args.html):
    arg_parser.error("Output type needs to be specified")
if (args.pdf and args.html):
    arg_parser.error("Both output types cannot be specified")

def render_html(dmx_venue, dmx_universes, dmx_universes_occupancy):
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.dirname(os.path.realpath(__file__)))
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "dmx.jinja2"
    template = template_env.get_template(template_file)
    output_text = template.render(
        dmx_venue=dmx_venue,
        dmx_universes=dmx_universes,
        dmx_universes_occupancy=dmx_universes_occupancy,
        gen={
        'date': datetime.datetime.now(datetime.timezone.utc).astimezone()
        }
    )
    return output_text

if __name__ == "__main__":
    print("Python VRSL DMX Patch Set Generator")
    print(f"VRSL file: {args.vrsl_json}")
    print(f"Extras file: {args.extras}")
    print(f"Output file: {args.outfile}")
    print(f"Output type: {'pdf' if args.pdf else 'html'}")

    # Load VRSL stuff
    with open(args.vrsl_json, 'r') as f:
        dmx_vrsl = json.load(f)
        dmx_vrsl = dmx_vrsl['fixtures']

    # Load extras stuff
    with open(args.extras, 'r') as f:
        dmx_extras = yaml.safe_load(f)

    dmx_universes = {}
    dmx_universes_occupancy = {}

    # Cycle all universes and fill them
    for universe in range(1, MAX_DMX_UNIVERSES, 1):
        fixtures_in_universe = []
        fixtures_occupancy_in_universe = {}
        # pre-fill the occupancy
        for i in range(1, MAX_DMX_CHANNELS, 1):
            fixtures_occupancy_in_universe[i] = {'used': False, 'main_channel': True}

        # cycle all VRSL fixtures
        for fixture in dmx_vrsl:
            if (fixture['universe'] == universe):
                fixtures_in_universe.append(fixture)
                # fill occupancy
                fixtures_occupancy_in_universe[fixture['channel']] = {'used': True, 'main_channel': True}
                for channelId in range(fixture['channel'] + 1, fixture['channel'] + len(fixture['channelNames']), 1):
                    fixtures_occupancy_in_universe[channelId] = {'used': True, 'main_channel': False}
        # cycle all gpu readback fixtures
        for fixture in dmx_extras['gpu_readback_fixtures']:
            if (fixture['universe'] == universe):
                fixtures_in_universe.append(fixture)
                # fill occupancy
                fixtures_occupancy_in_universe[fixture['channel']] = {'used': True, 'main_channel': True}
                for channelId in range(fixture['channel'] + 1, fixture['channel'] + len(fixture['channelNames']), 1):
                    fixtures_occupancy_in_universe[channelId] = {'used': True, 'main_channel': False}
        # sort by channel
        fixtures_in_universe = sorted(fixtures_in_universe, key=lambda x: x['channel'])
        # add to the thing
        dmx_universes[universe] = fixtures_in_universe
        dmx_universes_occupancy[universe] = fixtures_occupancy_in_universe

    html_output = render_html(dmx_extras['venue'], dmx_universes, dmx_universes_occupancy)
    if (args.html):
        with open(args.outfile, 'w') as f:
            f.write(html_output)
        print(f"File {args.outfile} written.")

    if (args.pdf):
        print("Not implemented :<")
