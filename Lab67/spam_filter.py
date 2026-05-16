import math

import pandas as pd

from naiveBayesClassifier import NaiveBayesFilter


DATASET_PATH = 'SMSSpamCollection.csv'
LABELS = ['ham', 'spam']


def clean_messages(messages):
    return messages.str.replace(r'\W', ' ', regex=True).str.lower().str.split()


def train_test_split(df, train_ratio=0.8, random_state=1):
    data_randomized = df.sample(frac=1, random_state=random_state)
    split_index = round(len(data_randomized) * train_ratio)
    training_set = data_randomized[:split_index].reset_index(drop=True)
    test_set = data_randomized[split_index:].reset_index(drop=True)
    return training_set, test_set


def confusion_matrix(true_labels, predicted_labels):
    matrix = {
        actual: {predicted: 0 for predicted in LABELS}
        for actual in LABELS
    }
    for actual, predicted in zip(true_labels, predicted_labels):
        matrix[actual][predicted] += 1
    return matrix


def class_metrics(true_labels, predicted_labels):
    matrix = confusion_matrix(true_labels, predicted_labels)
    rows = []
    total_correct = 0
    total = len(true_labels)

    for label in LABELS:
        true_positive = matrix[label][label]
        predicted_as_label = sum(matrix[actual][label] for actual in LABELS)
        actual_label = sum(matrix[label][predicted] for predicted in LABELS)

        precision = true_positive / predicted_as_label if predicted_as_label else 0
        recall = true_positive / actual_label if actual_label else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0
        )
        rows.append({
            'Class': label,
            'Precision': precision,
            'Recall': recall,
            'F1-score': f1,
            'Support': actual_label,
        })
        total_correct += true_positive

    return rows, total_correct / total


def top_indicative_words(model, n=10):
    rows = []
    for word in model.vocabulary:
        spam_probability = model.parameters_spam[word]
        ham_probability = model.parameters_ham[word]
        log_ratio = math.log(spam_probability / ham_probability)
        rows.append({
            'Word': word,
            'P(word|spam)': spam_probability,
            'P(word|ham)': ham_probability,
            'Log ratio': log_ratio,
        })

    top_spam = sorted(rows, key=lambda row: row['Log ratio'], reverse=True)[:n]
    top_ham = sorted(rows, key=lambda row: row['Log ratio'])[:n]
    return top_spam, top_ham


def print_dataset_summary(df, training_set, test_set, model):
    print('\n=== Dataset Summary ===')
    print(f'Total messages: {len(df)}')
    print(f'Training messages: {len(training_set)}')
    print(f'Test messages: {len(test_set)}')
    print(f'Vocabulary size: {len(model.vocabulary)}')
    print(f'Total spam word occurrences in training set: {model.n_words_spam}')
    print(f'Total ham word occurrences in training set: {model.n_words_ham}')
    print(f'P(spam): {model.p_spam:.6f}')
    print(f'P(ham): {model.p_ham:.6f}')

    print('\n=== Class Distribution ===')
    distribution = pd.DataFrame({
        'Full dataset': df['Label'].value_counts(),
        'Training set': training_set['Label'].value_counts(),
        'Test set': test_set['Label'].value_counts(),
    }).reindex(LABELS)
    print(distribution.to_string())


def print_metrics_table(title, true_labels, predicted_labels):
    rows, accuracy = class_metrics(true_labels, predicted_labels)
    print(f'\n=== {title} Metrics ===')
    print(f'Accuracy from score(): {accuracy:.6f}')
    metrics_df = pd.DataFrame(rows)
    formatted = metrics_df.copy()
    for column in ['Precision', 'Recall', 'F1-score']:
        formatted[column] = formatted[column].map(lambda value: f'{value:.4f}')
    print(formatted.to_string(index=False))

    matrix = confusion_matrix(true_labels, predicted_labels)
    print(f'\n=== {title} Confusion Matrix ===')
    matrix_df = pd.DataFrame(matrix).T[LABELS]
    matrix_df.index.name = 'Actual'
    matrix_df.columns = [f'Predicted {label}' for label in LABELS]
    print(matrix_df.to_string())


def print_probability_examples(messages, true_labels, predicted_labels, probabilities, n=5):
    print('\n=== Sample Test Predictions ===')
    rows = []
    for index, (message, true_label, predicted_label, probability) in enumerate(
        zip(messages, true_labels, predicted_labels, probabilities)
    ):
        if index == n:
            break
        rows.append({
            'Index': index,
            'True': true_label,
            'Predicted': predicted_label,
            'P(ham|x)': f'{probability[0]:.6f}',
            'P(spam|x)': f'{probability[1]:.6f}',
            'Cleaned message': ' '.join(message[:12]),
        })
    print(pd.DataFrame(rows).to_string(index=False))


def print_top_words(model):
    top_spam, top_ham = top_indicative_words(model)

    print('\n=== Top Spam-Indicative Words ===')
    spam_df = pd.DataFrame(top_spam)
    for column in ['P(word|spam)', 'P(word|ham)', 'Log ratio']:
        spam_df[column] = spam_df[column].map(lambda value: f'{value:.6f}')
    print(spam_df.to_string(index=False))

    print('\n=== Top Ham-Indicative Words ===')
    ham_df = pd.DataFrame(top_ham)
    for column in ['P(word|spam)', 'P(word|ham)', 'Log ratio']:
        ham_df[column] = ham_df[column].map(lambda value: f'{value:.6f}')
    print(ham_df.to_string(index=False))


def try_sklearn_comparison(
    X_train,
    y_train,
    X_test,
    y_test,
    custom_train_accuracy,
    custom_test_accuracy,
):
    try:
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.naive_bayes import MultinomialNB
    except ImportError:
        print('\n=== Sklearn Comparison ===')
        print('scikit-learn is not installed in this environment.')
        print('Install scikit-learn to compare against MultinomialNB.')
        return

    vectorizer = CountVectorizer(token_pattern=r'(?u)\b\w+\b')
    X_train_counts = vectorizer.fit_transform([' '.join(message) for message in X_train])
    X_test_counts = vectorizer.transform([' '.join(message) for message in X_test])

    sklearn_model = MultinomialNB(alpha=1)
    sklearn_model.fit(X_train_counts, y_train)
    sklearn_train_predictions = sklearn_model.predict(X_train_counts)
    sklearn_predictions = sklearn_model.predict(X_test_counts)
    _, sklearn_train_accuracy = class_metrics(y_train, sklearn_train_predictions)
    _, sklearn_accuracy = class_metrics(y_test, sklearn_predictions)

    print('\n=== Sklearn Comparison ===')
    print('Custom NaiveBayesFilter and sklearn MultinomialNB both use alpha=1.')
    comparison_df = pd.DataFrame([
        {
            'Model': 'Custom NaiveBayesFilter',
            'Training accuracy': f'{custom_train_accuracy:.6f}',
            'Test accuracy': f'{custom_test_accuracy:.6f}',
        },
        {
            'Model': 'Sklearn MultinomialNB',
            'Training accuracy': f'{sklearn_train_accuracy:.6f}',
            'Test accuracy': f'{sklearn_accuracy:.6f}',
        },
    ])
    print(comparison_df.to_string(index=False))


def main():
    df = pd.read_csv(DATASET_PATH, sep='\t', header=None, names=['Label', 'SMS'])
    training_set, test_set = train_test_split(df)

    X_train = clean_messages(training_set['SMS'])
    y_train = training_set['Label']
    X_test = clean_messages(test_set['SMS'])
    y_test = test_set['Label']

    model = NaiveBayesFilter(alpha=1)
    model.fit(X_train, y_train)

    train_predictions = model.predict(X_train)
    test_probabilities = model.predict_proba(X_test)
    test_predictions = model.predict(X_test)
    _, custom_train_accuracy = class_metrics(y_train, train_predictions)
    _, custom_test_accuracy = class_metrics(y_test, test_predictions)

    print_dataset_summary(df, training_set, test_set, model)
    print_metrics_table('Training Set', y_train, train_predictions)
    print_metrics_table('Test Set', y_test, test_predictions)
    print_probability_examples(
        X_test,
        y_test,
        test_predictions,
        test_probabilities,
    )
    print_top_words(model)
    try_sklearn_comparison(
        X_train,
        y_train,
        X_test,
        y_test,
        custom_train_accuracy,
        custom_test_accuracy,
    )


if __name__ == '__main__':
    main()
