#!/usr/bin/env python
#-*- coding: utf-8 -*-
# coding: utf-8


"""
Author: Arnaud Ferré
Mail: arnaud.ferre.pro@gmail.com
Description: If you have trained the module_train on a training set (terms associated with concept(s)), you can do here
    a prediction of normalization with a test set (new terms without pre-association with concept). NB : For now, you
    can only use a Sklearn object from the class LinearRegression.
    If you want to cite this work in your publication or to have more details:
    http://www.aclweb.org/anthology/W17-2312.
Dependency: Numpy lib (available with Anaconda)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


#######################################################################################################
# Import modules & set up logging
#######################################################################################################
import numpy
from utils import word2term, onto
from optparse import OptionParser
import json
from sklearn.externals import joblib

#######################################################################################################
# Functions
#######################################################################################################
def getCosSimilarity(vec1, vec2):
    """
    Description: Calculates the cosine similarity between 2 vectors.
    """
    from scipy import spatial
    result = 1 - spatial.distance.cosine(vec1, vec2)
    return result


def getNearestConcept(vecTerm, vso):
    """
    Description: For now, calculates all the cosine similarity between a vector and the concept-vectors of the VSO,
        then, gives the nearest.
    :param vecTerm: A vector in the VSO.
    :param vso: A VSO (dict() -> {"id" : [vector], ...}
    :return: the id of the nearest concept.
    """
    max = 0
    mostSimilarConcept = None
    for id_concept in vso.keys():
        dist = getCosSimilarity(vecTerm, vso[id_concept])
        if dist > max:
            max = dist
            mostSimilarConcept = id_concept
    return mostSimilarConcept



def predictor(vst_onlyTokens, dl_terms, vso, transformationParam, symbol="___"):
    """
    Description: From a calculated linear projection from the training module, applied it to predict a concept for each
        terms in parameters (dl_terms).
    :param vst_onlyTokens: An initial VST containing only tokens and associated vectors.
    :param dl_terms: A dictionnary with id of terms for key and raw form of terms in value.
    :param vso: A VSO (dict() -> {"id" : [vector], ...}
    :param transformationParam: LinearRegression object from Sklearn. Use the one calculated by the training module.
    :param symbol: Symbol delimiting the different token in a multi-words term.
    :return: A list of tuples containing : ("term form", "term id", "predicted concept id") and a list of unknown tokens
        containing in the terms from dl_terms.
    """
    lt_predictions = list()

    vstTerm, l_unknownToken = word2term.wordVST2TermVST(vst_onlyTokens, dl_terms)

    result = dict()

    vsoTerms = dict()
    for id_term in dl_terms.keys():
        termForm = word2term.getFormOfTerm(dl_terms[id_term], symbol)
        x = vstTerm[termForm].reshape(1, -1)
        vsoTerms[termForm] = transformationParam.predict(x)[0]

        result[termForm] = getNearestConcept(vsoTerms[termForm], vso)

    for id_term in dl_terms.keys():
        termForm = word2term.getFormOfTerm(dl_terms[id_term], symbol)
        prediction = (termForm, id_term, result[termForm])
        lt_predictions.append(prediction)

    return lt_predictions, l_unknownToken


def loadJSON(filename):
    f = open(filename)
    result = json.load(f)
    f.close()
    return result;


class Predictor(OptionParser):
    def __init__(self):
        OptionParser.__init__(self, usage='usage: %prog [options]')
        self.add_option('--word-vectors', action='store', type='string', dest='word_vectors', help='path to word vectors file as produced by word2vec')
        self.add_option('--terms', action='store', type='string', dest='terms', help='path to terms file in JSON format (map: id -> array of tokens)')
        self.add_option('--ontology', action='store', type='string', dest='ontology', help='path to ontology file in OBO format')
        self.add_option('--regression-matrix', action='store', type='string', dest='regression_matrix', help='path to the regression matrix file as produced by the training module')
        self.add_option('--output', action='store', type='string', dest='output', help='file where to write predictions')
        
    def run(self):
        options, args = self.parse_args()
        if len(args) > 0:
            raise Exception('stray arguments: ' + ' '.join(args))
        if options.word_vectors is None:
            raise Exception('missing --word-vectors')
        if options.terms is None:
            raise Exception('missing --terms')
        if options.ontology is None:
            raise Exception('missing --ontology')
        if options.regression_matrix is None:
            raise Exception('missing --regression-matrix')
        if options.output is None:
            raise Exception('missing --output')
        word_vectors = loadJSON(options.word_vectors)
        terms = loadJSON(options.terms)
        ontology = onto.loadOnto(options.ontology)
        vso = onto.ontoToVec(ontology)
        regression_matrix = joblib.load(options.regression_matrix)
        prediction, _ = predictor(word_vectors, terms, vso, regression_matrix)
        f = open(options.output, 'w')
        for _, term_id, concept_id in prediction:
            f.write('%s\t%s\n' % (term_id, concept_id))
        f.close()

if __name__ == '__main__':
    Predictor().run()
