"""Unit tests for the counter module.
"""

import unittest

import mock

from app.models.association_objects import DependencyInSentence
from app.models.association_objects import WordInSentence
from app.models.dependency import Dependency
from app.models.counts import DependencyCount
from app.models.counts import WordCount
from app.models.document import Document
from app.models.project import Project
from app.preprocessor import counter


class CounterTests(unittest.TestCase):
    """Test the counting functions.
    """
    @mock.patch.object(counter, "count_bigrams", autospec=True)
    @mock.patch.object(counter, "count_documents", autospec=True)
    @mock.patch.object(counter, "count_dependencies", autospec=True)
    @mock.patch.object(counter, "count_words", autospec=True)
    def test_count_all(self, mock_count_words, mock_count_dependencies,
            mock_count_documents, mock_count_bigrams):
        """Test the count_all function.
        """
        mock_project = mock.create_autospec(Project)
        interval = 4

        counter.count_all(mock_project, interval)

        mock_count_words.assert_called_once_with(mock_project, interval)
        mock_count_dependencies.assert_called_once_with(mock_project, interval)
        mock_count_documents.assert_called_once_with(mock_project, interval)
        mock_count_bigrams.assert_called_once_with(mock_project, interval)

    @mock.patch("app.preprocessor.counter.ProjectLogger", autospec=True)
    @mock.patch("app.preprocessor.counter.db", autospec=True)
    def test_count_documents(self, mock_db, mock_project_logger):
        """Test the count_documents method
        """
        interval =  2

        mock_project = mock.create_autospec(Project)
        mock_project.get_documents.return_value = []

        for i in range(0, interval * 2 + 1):
            document = mock.create_autospec(Document)
            document.all_sentences = range(0, 5)
            mock_project.get_documents.return_value.append(document)

        counter.count_documents(mock_project, interval)

        assert mock_db.session.commit.call_count == interval + 1

        for document in mock_project.get_documents.return_value:
            assert document.sentence_count == 5

    @mock.patch("app.preprocessor.counter.Dependency", autospec=True)
    @mock.patch("app.preprocessor.counter.ProjectLogger", autospec=True)
    @mock.patch("app.preprocessor.counter.db", autospec=True)
    def test_count_dependencies(self, mock_db, mock_project_logger,
            mock_dependency):
        """Test the count_dependencies method.
        """
        interval = 2

        mock_dependency_count = mock.create_autospec(DependencyCount)
        mock_dependency.query.get.return_value.get_counts.return_value = \
                mock_dependency_count

        rows = []

        for i in range(0, interval * 2 + 1):
            row = mock.create_autospec(DependencyInSentence)
            row.dependency_id = i
            row.document_count = 2
            row.sentence_count = 5
            rows.append(row)

        mock_db.session.execute.return_value.fetchall.return_value = rows

        mock_project = mock.create_autospec(Project)

        counter.count_dependencies(mock_project, interval)

        dependency_id_calls = [mock.call(i) for i in range(0, interval * 2 + 1)]

        assert mock_db.session.commit.call_count == interval + 1
        assert mock_dependency.query.get.call_args_list == dependency_id_calls
        assert mock_dependency_count.document_count == 2
        assert mock_dependency_count.sentence_count == 5

    @mock.patch("app.preprocessor.counter.Word", autospec=True)
    @mock.patch("app.preprocessor.counter.ProjectLogger", autospec=True)
    @mock.patch("app.preprocessor.counter.db", autospec=True)
    def test_count_words(self, mock_db, mock_project_logger,
            mock_word):
        """Test the count_words method.
        """
        interval = 2

        mock_word_count = mock.create_autospec(WordCount)
        mock_word.query.get.return_value.get_counts.return_value = \
                mock_word_count

        rows = []

        for i in range(0, interval * 2 + 1):
            row = mock.create_autospec(WordInSentence)
            row.word_id = i
            row.sentence_count = 5
            rows.append(row)

        mock_db.session.execute.return_value.fetchall.return_value = rows

        mock_project = mock.create_autospec(Project)

        counter.count_words(mock_project, interval)

        word_id_calls = [mock.call(i) for i in range(0, interval * 2 + 1)]

        assert mock_db.session.commit.call_count == interval + 1
        assert mock_word.query.get.call_args_list == word_id_calls
        assert mock_word_count.sentence_count == 5

