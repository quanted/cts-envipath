# Copyright 2020 enviPath UG & Co. KG
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from collections import defaultdict
from enviPath_python.objects import Pathway, Setting


class MultiGenUtils(object):

    @staticmethod
    def evaluate(pathway: Pathway, setting: Setting):
        """
        Takes an pathway and uses the setting to predict a pathway with the exact same root node and compares
        the resulting pathway against the provided one.
        :param pathway: The pathway that is tried to predict.
        :param setting: The setting used for prediction
        :return:
        """
        # TODO
        pass

    @staticmethod
    def assemble_upsream(pathway: Pathway) -> dict:
        res = defaultdict(set)
        for edge in pathway.get_edges():
            res[edge.get_end_nodes].add(edge.get_start_nodes())
        return res

    @staticmethod
    def assemble_eval_weights(pathway: Pathway) -> defaultdict[set]:
        res = defaultdict(lambda x: 1)
        for node in pathway.get_nodes():
            res[node] = 1 / 2 ** node.get_depth()
        return res

    @staticmethod
    def compare_pathways(pred: Pathway, data: Pathway):
        correct_ndoes = set()
        incorrect_nodes = set()
        correct_edges = set()
        incorrect_edges = set()

        pred_upstream = MultiGenUtils.assemble_upsream(pred)
        pred_eval_weights = MultiGenUtils.assemble_eval_weights(pred)
        data_upstream = MultiGenUtils.assemble_upsream(data)
        data_eval_weights = MultiGenUtils.assemble_eval_weights(data)

        tp_pred = 0.0
        tp_data = 0.0
        fp = 0.0
        fn = 0.0

        for node, outgoing_nodes in data_upstream.items():
            if node in pred_upstream:
                if node.get_depth() == 1:
                    # No upstream nodes available as this is the root
                    continue
                else:
                    if data_upstream[node].intersection(pred_upstream[node]):
                        correct_ndoes.add(node)
                        for edge in data.get_edges():
                            if node in edge.get_end_nodes:
                                correct_edges.add(edge)

                        tp_pred = tp_pred + pred_eval_weights[node]
                    else:  # No overlap
                        # TODO duplicate
                        fn = fn + pred_eval_weights[node]
                        incorrect_nodes.add(node)
                        for edge in data.get_edges():
                            if node in edge.get_end_nodes:
                                incorrect_edges.add(edge)
            else:
                # TODO duplicate
                fn = fn + pred_eval_weights[node]
                incorrect_nodes.add(node)
                for edge in data.get_edges():
                    if node in edge.get_end_nodes:
                        incorrect_edges.add(edge)

        return tp_pred, tp_data, fp, fn
