import numpy as np
import pandas as pd


class NaiveBayesFilter:
    def __init__(self, alpha=1):
        self.data = []
        self.vocabulary = []
        self.p_spam = 0
        self.p_ham = 0
        self.alpha = alpha
        self.n_words_spam = 0
        self.n_words_ham = 0
        self.parameters_spam = {}
        self.parameters_ham = {}

    def fit(self, X, y):
        # Problem 1: build the bag-of-words vocabulary and count table.
        vocab = set()
        for message in X:
            for word in message:
                vocab.add(word)
        self.vocabulary = sorted(vocab)

        n_samples = len(y)
        n_spam = sum(1 for label in y if label == 'spam')
        n_ham = sum(1 for label in y if label == 'ham')

        # Equations 1.3 and 1.4: class prior probabilities.
        self.p_spam = n_spam / n_samples
        self.p_ham = n_ham / n_samples

        rows = []
        for message, label in zip(X, y):
            word_counts = {word: 0 for word in self.vocabulary}
            for word in message:
                if word in word_counts:
                    word_counts[word] += 1
            word_counts['Label'] = label
            rows.append(word_counts)

        self.data = pd.DataFrame(rows)

        spam_messages = self.data[self.data['Label'] == 'spam']
        ham_messages = self.data[self.data['Label'] == 'ham']

        self.n_words_spam = int(spam_messages[self.vocabulary].values.sum())
        self.n_words_ham = int(ham_messages[self.vocabulary].values.sum())

        # Equation 1.5 with Laplace smoothing:
        # P(word | class) = (count(word, class) + alpha)
        #                 / (total_words(class) + alpha * vocabulary_size)
        n_vocab = len(self.vocabulary)
        self.parameters_spam = {}
        self.parameters_ham = {}
        for word in self.vocabulary:
            n_word_spam = spam_messages[word].sum()
            n_word_ham = ham_messages[word].sum()
            self.parameters_spam[word] = (
                n_word_spam + self.alpha
            ) / (self.n_words_spam + self.alpha * n_vocab)
            self.parameters_ham[word] = (
                n_word_ham + self.alpha
            ) / (self.n_words_ham + self.alpha * n_vocab)

        return self.data

    def predict_proba(self, X):
        # Problem 2: compute [P(ham | x), P(spam | x)] for each message.
        proba = []
        for message in X:
            log_p_spam = np.log(self.p_spam)
            log_p_ham = np.log(self.p_ham)

            for word in message:
                if word in self.parameters_spam:
                    log_p_spam += np.log(self.parameters_spam[word])
                    log_p_ham += np.log(self.parameters_ham[word])

            # Normalize the two log scores into probabilities.
            max_log = max(log_p_spam, log_p_ham)
            p_spam_x = np.exp(log_p_spam - max_log)
            p_ham_x = np.exp(log_p_ham - max_log)
            total = p_spam_x + p_ham_x

            proba.append([p_ham_x / total, p_spam_x / total])

        return proba

    def predict(self, X):
        # Problem 3: choose the class with the larger posterior probability.
        predictions = []
        for p_ham_given_x, p_spam_given_x in self.predict_proba(X):
            if p_spam_given_x > p_ham_given_x:
                predictions.append('spam')
            else:
                predictions.append('ham')
        return predictions

    def score(self, true_labels, predict_labels):
        # Problem 4: the lab names this recall, but the formula is accuracy.
        true_list = list(true_labels)
        pred_list = list(predict_labels)
        matched = sum(1 for t, p in zip(true_list, pred_list) if t == p)
        return matched / len(true_list)
