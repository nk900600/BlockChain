from flask import Flask, jsonify, request
import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4

from blockchain import Blockchain

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    lastBlock = blockchain.last_block
    newProof = blockchain.proof_of_work(lastBlock["proof"])

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    previous_hash = blockchain.hash(lastBlock)
    block = blockchain.new_block(newProof, previous_hash)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    body = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in body for k in required):
        return 'Missing values', 400
    index = blockchain.new_transaction(body["sender"], body["recipient"], body["amount"])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route("/chain", methods=["GET"])
def full_chain():
    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    }
    return jsonify(response)


@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    body = request.get_json()
    nodes = body.get("nodes")
    if nodes is None:
        return "Error: Please supply a valid list"
    for node in nodes:
        blockchain.register_node(node)

    response = {
        "message": "New nodes added",
        "total_nodes": list(blockchain.nodes)
    }
    return jsonify(response), 201


@app.route("/nodes/resolve", methods=["GET"])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
        return jsonify(response), 200
    response = {
        'message': 'Our chain was authoritative',
        'new_chain': blockchain.chain
    }
    return jsonify(response), 200


app.run(port=3000)
