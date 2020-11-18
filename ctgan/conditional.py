import numpy as np


class ConditionalGenerator(object):
    # ConditionalGenerator does the sampling of categorical columns.
    # output_info comes from transformer, basically whether the column is continuous or categorical.
    def __init__(self, data, output_info, log_frequency, trans="VGM", use_cond_gen=True):

        if use_cond_gen:

            self.model = []

            start = 0
            skip = False
            max_interval = 0
            counter = 0
            for item in output_info:
                # NOTE:
                # in transformer.py, the output_info of _fit_continuous
                # contains tanh and softmax for VGM transformation
                # Thus, the reason for skip = True in the for loop.
                # the output_info of _fit_discrete contains only softmax.
                if item[1] == 'tanh':
                    start += item[0]
                    if trans == "VGM":
                        skip = True
                    continue

                elif item[1] == 'softmax':
                    if skip:
                        skip = False
                        start += item[0]
                        continue

                    end = start + item[0]
                    max_interval = max(max_interval, end - start)
                    counter += 1
                    self.model.append(np.argmax(data[:, start:end], axis=-1))
                    start = end

                else:
                    assert 0

            assert start == data.shape[1]

            # NOTE:
            # n_col is the number of categorical columns.
            # n_opt is total number of categories in all categorical columns.
            self.interval = []
            self.n_col = 0
            self.n_opt = 0
            skip = False
            start = 0
            self.p = np.zeros((counter, max_interval))
            for item in output_info:
                if item[1] == 'tanh':
                    if trans == "VGM":
                        skip = True
                    start += item[0]
                    continue
                elif item[1] == 'softmax':
                    if skip:
                        start += item[0]
                        skip = False
                        continue
                    end = start + item[0]
                    tmp = np.sum(data[:, start:end], axis=0)

                    # NOTE:
                    # See explanation in Figure 2 of the paper.
                    # "training data are sampled according to the log-frequency of each category,
                    # thus CTGAN can evenly explore all possible discrete values."
                    if log_frequency:
                        tmp = np.log(tmp + 1)
                    tmp = tmp / np.sum(tmp)

                    # NOTE: p records the probability mass function of corresponding categorical columns.
                    self.p[self.n_col, :item[0]] = tmp
                    self.interval.append((self.n_opt, item[0]))
                    self.n_opt += item[0]
                    self.n_col += 1
                    start = end
                else:
                    assert 0

            self.interval = np.asarray(self.interval)

        else:
            self.n_col = 0
            self.n_opt = 0

    def random_choice_prob_index(self, idx):
        # NOTE: inverse transform sampling
        a = self.p[idx]
        r = np.expand_dims(np.random.rand(a.shape[0]), axis=1)
        return (a.cumsum(axis=1) > r).argmax(axis=1)

    def sample(self, batch):
        # NOTE: sample is used for training. See synthesizer fit function
        if self.n_col == 0:
            return None

        # NOTE:
        # idx: randomly choose one of the categorical columns
        # vec1: example in the paper, see Figure 2, the one-hot encoded vector of D1 and D2.
        # mask1: which categorical column is selected.
        # opt1prime: the selected category of corresponding categorical column.

        batch = batch
        idx = np.random.choice(np.arange(self.n_col), batch)

        vec1 = np.zeros((batch, self.n_opt), dtype='float32')
        mask1 = np.zeros((batch, self.n_col), dtype='float32')
        mask1[np.arange(batch), idx] = 1
        opt1prime = self.random_choice_prob_index(idx)
        opt1 = self.interval[idx, 0] + opt1prime
        vec1[np.arange(batch), opt1] = 1

        return vec1, mask1, idx, opt1prime

    def sample_zero(self, batch):
        # NOTE: sample_zero is used for synthesizing data after ctgan is trained.
        # See synthesizer sample function.
        if self.n_col == 0:
            return None

        vec = np.zeros((batch, self.n_opt), dtype='float32')
        idx = np.random.choice(np.arange(self.n_col), batch)
        for i in range(batch):
            col = idx[i]
            pick = int(np.random.choice(self.model[col]))
            vec[i, pick + self.interval[col, 0]] = 1

        return vec

    def generate_cond_from_condition_column_info(self, condition_info, batch):
        # NOTE: generate_cond_from_condition_column_info is used for synthesizing data after ctgan is trained.
        # See synthesizer sample function, when condition_column and condition_value are both given.
        vec = np.zeros((batch, self.n_opt), dtype='float32')
        id = self.interval[condition_info["discrete_column_id"]][0] + condition_info["value_id"]
        vec[:, id] = 1
        return vec
