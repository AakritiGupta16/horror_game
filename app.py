from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import openai

app = Flask(__name__)
app.secret_key = 'your_key'  # Replace with your own secret key

openai.api_key = "your_api_key"

def limit_sentences(text, num_sentences):
    sentences = text.split('. ')
    limited_text = '. '.join(sentences[:num_sentences])
    return limited_text


@app.route('/')
def home():
    session.clear()
    return render_template('index.html')


@app.route('/play', methods=['POST'])
def play_game():
    result = ''
    player_input = request.form.get('player_input')
    player_name = request.form.get('player_name')

    if 'player_name' not in session or not session['player_name']:  # check if player_name is not set or is empty
        if player_name:  # if player_name form input is not empty
            session['player_name'] = player_name
            session['moves'] = 0
            session['has_key'] = False
            session['game_over'] = False
            session['options'] = []
            session['current_location'] = ''
            session['state'] = ''

            # Here you can include a starting message to the player
            return jsonify(
                {'text': f"Welcome to the game, {session['player_name']}! Your horrific adventure begins now...",
                 'options': []})
        else:  # player_name form input is empty, do not proceed
            return jsonify({'text': "Please enter your name to start the game.", 'options': []})
    else:
        session['moves'] += 1  # Increase the move count
        if session['moves'] > 10:
            session['game_over'] = True
            return jsonify({'text': "You feel the ground beneath you collapse. You fall into a pit and your adventure "
                                    "ends here.", 'options': []})

        else:
            if session['options'] and player_input is not None:  # Make sure player_input is not None
                option_text = session['options'][int(player_input) - 1]
                if "key" in option_text and session['moves'] > 3:
                    session['has_key'] = True

                if "lock" in option_text and session['has_key'] and session['moves'] > 4:
                    session['game_over'] = True
                    return "You have successfully found the lock and use the key to open it. You have escaped and won the " \
                           "game! "
            else:
                option_text = player_input

            # generate situations
            if session['moves'] == 1:
                session['state'] = "starting point"
                situation_prompt = f"The player named {session.get('player_name', '')} is starting his/her adventure. " \
                                   f"Describe the starting surroundings in a horror setting. Don't start a sentence if it is "\
                       f"going to exceed the max_tokens defined. Replace 'the player' with 'you'. Write it as a paragraph. "
            elif 7 <= session['moves'] < 9:
                session['state'] = "towards the end"
                situation_prompt = f"The player named {session.get('player_name', '')} has chosen option {option_text} in the situation: {session.get('current_location', '')}."\
                       f"Build up on the current situation accordingly. All the situations must be linked with each other to form a story. Make the story as horror filled as possible. Replace 'the player' with 'you'. Write it as a paragraph. Don't leave a sentence Lead the player towards a key in a horror setting."
            elif session['moves'] == 10:
                session['state'] = "end"
                situation_prompt = f"The player named {session.get('player_name', '')} has chosen option {option_text} in the situation: {session.get('current_location', '')}."\
                       f"Build up on the current situation accordingly. All the situations must be linked with each other to form a story. Make the story as horror filled as possible.  "\
                       f" Replace 'the player' with 'you'. Write it as a paragraph. Lead the player towards a lock in a horror setting."
            else:
                session['state'] = "middle"
                situation_prompt = f"The player named {session.get('player_name', '')} has chosen option {option_text} in the situation: {session.get('current_location', '')}."\
                       f"Build up on the current situation accordingly. All the situations must be linked with each other to form a story. Make the story as horror filled as possible."\
                       f"Replace 'the player' with 'you'. Write it as a very small paragraph."

            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=situation_prompt,
                temperature=0.5,
                max_tokens=100
            )

            result = response.choices[0].text.strip()
            session['current_location'] = limit_sentences(result, 5)


            # generate options
            if session['moves'] >= 7:
                options_prompt = f"In {session['current_location']}, what are the three options the player can choose from? The "
                f"options should be horror and based on the current situation of the player. Do not repeat the "
                f"options in "
                f"different situations. Each option should be a single line and not numbered. Options for the last three situations should lead the player towards a key "
                f"and lock."

            else:
                options_prompt = f"In {session['current_location']}, what are the three options the player can choose " \
                                 f"from? The options should be horror and based on the current situation of the " \
                                 f"player. Each option should be a single line and not numbered. Do not repeat the options in different situations. Do not provide options " \
                                 f"with 'lock' or 'key'."

            options_response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=options_prompt,
                temperature=0.6,
                max_tokens=100
            )
            session['options'] = options_response.choices[0].text.strip().split("\n")

        response = {
            'text': session['current_location'],
            'options': session['options']
        }
        return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
