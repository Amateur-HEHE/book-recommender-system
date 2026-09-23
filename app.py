from flask import Flask, render_template, request
import pickle
import numpy as np

popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

app = Flask(__name__)

# One row per title, so lookups are fast
book_info = books.drop_duplicates('Book-Title').set_index('Book-Title')
TITLES = list(pt.index)
LOWER_TITLES = pt.index.str.lower()


def https(url):
    # Amazon cover URLs are http; this avoids mixed-content warnings when deployed on https
    return url.replace('http://', 'https://') if isinstance(url, str) else url


@app.route('/')
def index():
    top_books = [
        {
            'title': t,
            'author': a,
            'image': https(i),
            'votes': int(v),
            'rating': round(float(r), 1),
        }
        for t, a, i, v, r in zip(
            popular_df['Book-Title'],
            popular_df['Book-Author'],
            popular_df['Image-URL-M'],
            popular_df['num_ratings'],
            popular_df['avg_rating'],
        )
    ]
    return render_template('index.html', books=top_books, titles=TITLES)


@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html', titles=TITLES)


@app.route('/recommend_books', methods=['POST'])
def recommend():
    user_input = (request.form.get('user_input') or '').strip()
    matches = np.where(LOWER_TITLES == user_input.lower())[0]

    # Book not in the dataset: show a helpful message instead of crashing
    if len(matches) == 0:
        return render_template('recommend.html', titles=TITLES,
                               query=user_input, not_found=True, data=[])

    idx = matches[0]
    similar_items = sorted(enumerate(similarity_scores[idx]),
                           key=lambda x: x[1], reverse=True)[1:9]

    data = []
    for i, _score in similar_items:
        title = pt.index[i]
        row = book_info.loc[title]
        data.append({
            'title': title,
            'author': row['Book-Author'],
            'image': https(row['Image-URL-M']),
        })

    return render_template('recommend.html', titles=TITLES,
                           query=pt.index[idx], data=data)


if __name__ == '__main__':
    app.run(debug=True)
