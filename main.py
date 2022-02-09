import argparse
import sys
import configparser
import itertools
import base64
from string import Template

parser = argparse.ArgumentParser(description='Convert environment files to kubernetes ConfigMap/Secret')
parser.add_argument('--name', metavar='name', nargs='?', type=str, default='my-secrets', help='Name of the configmap/secret store')
parser.add_argument('--kind', metavar='kind', nargs='?', type=str, default='ConfigMap', help='K8s kind: <ConfigMap | Secret>')
parser.add_argument('--env', metavar='.env', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='Environment input file, stdin by default')
parser.add_argument('--output', metavar='.yaml', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='Output file, stdout by default')

args = parser.parse_args()

config = configparser.ConfigParser()
config.optionxform = str
config.read_file(itertools.chain(['[global]'], args.env), source="env")
secrets = config.items('global')
args.env.close()

def loadFiles(secret):
  if (secret[1].startswith('filecontent=')):
    with open(secret[1][12:], 'r') as secretfile:
      data = secretfile.read()
      return [secret[0], data]
  return secret

secrets = map(loadFiles, secrets)

encodedSecrets = ['  {0}: {1}'.format(
    secret[0],
    base64.b64encode(secret[1].encode('utf-8')).decode('utf-8')
) for secret in secrets]

yamlTemplate = Template("""apiVersion: v1
kind: $kind
metadata:
  name: $name
type: Opaque
data:
$encodedSecrets""")
yamlOutput = yamlTemplate.substitute(name=args.name, kind=args.kind, encodedSecrets='\n'.join(encodedSecrets))

args.output.write(yamlOutput)
args.output.close()