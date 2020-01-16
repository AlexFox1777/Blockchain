import hashlib
import json
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request, render_template


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        A block should have:
        * Index
        * Timestamp
        * List of current transactions
        * The proof used to mine this block
        * The hash of the previous block

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'hash': previous_hash
        }

        # Reset the current list of transactions
        self.current_transactions = []
        # Append the chain to the block
        self.chain.append(block)
        # Return the new block
        return block

    def hash(self, block):
        """
        Creates a SHA-256 hash of a Block

        :param block": <dict> Block
        "return": <str>
        """

        # Use json.dumps to convert json into a string
        # Use hashlib.sha256 to create a hash
        # It requires a `bytes-like` object, which is what
        # .encode() does.
        # It convertes the string to bytes.
        # We must make sure that the Dictionary is Ordered,
        # or we'll have inconsistent hashes

        # TODO: Create the block_string
        block_str = json.dumps(block, sort_keys=True).encode()

        # TODO: Hash this string using sha256
        raw_hash = hashlib.sha256(block_str)

        hex_hash = raw_hash.hexdigest()

        # By itself, the sha256 function returns the hash in a raw string
        # that will likely include escaped characters.
        # This can be hard to read, but .hexdigest() converts the
        # hash to a string of hexadecimal characters, which is
        # easier to work with and understand

        # TODO: Return the hashed block string in hexadecimal format
        return hex_hash

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def valid_proof(block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 3
        leading zeroes?  Return true if the proof is valid
        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """
        # TODO
        guess = f"{block_string}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        print('guess ', guess_hash)
        return guess_hash[:3] == "000"

    def new_transaction(self, sender, recipient, amount):
        """
        Create  a new transaction to fo into the next mined block
        :param sender: <str> Name of the sender
        :param recipient: <str> Name of the recipient
        :param amount: <float> amount of transaction
        :return: <index> The index of the block that will hold transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in data for k in required):
        response = {'message': 'Missing values'}
        return jsonify(response), 400

    # create new transaction
    index = blockchain.new_transaction(data['sender'], data['recipient'], data['amount'])

    response = {'message': f' Transaction will post to block {index}'}

    return jsonify(response), 201


@app.route('/mine', methods=['POST'])
def mine():
    # receive client proof
    data = request.get_json()
    required = ['proof', 'id']
    if not all(k in data for k in required):
        response = {'message': 'Missing values'}
        return jsonify(response), 400

    l_block = blockchain.last_block
    last_block_string = json.dumps(l_block, sort_keys=True)

    if blockchain.valid_proof(last_block_string, data['proof']):
        previous_hash = blockchain.hash(l_block)
        new_block = blockchain.new_block(data['proof'], previous_hash)

        blockchain.new_transaction(sender=0, recipient=data['id'], amount=100)

        response = {
            "message": "Success",
            "new_block": new_block
        }

    else:
        response = {
            "message": "Proof is invalid or already submitted"
        }

    return jsonify(response), 200


@app.route('/last_block', methods=['GET'])
def last_block():
    response = {
        "last_block": blockchain.last_block
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET', 'POST'])
def full_chain():
    response = {
        "length": len(blockchain.chain),
        'chain': blockchain.chain
    }
    # return jsonify(response), 200
    print(request.method)
    amount = 0
    user_transactions = []
    if request.method == 'POST':
        name = request.form['id']
        print('name', name)
        for i in blockchain.chain:
            if len(i['transactions']) > 0:
                for o in i['transactions']:
                    print('transaction ', o)
                    if o['recipient'] == name:
                        user_transactions.append(o)
                        amount += o['amount']
        print(user_transactions)

    return render_template('wallet.html', chain=user_transactions, amount=amount)


# Run the program on port 5000
if __name__ == '__main__':
    app.run(host='localhost', port=2000)
