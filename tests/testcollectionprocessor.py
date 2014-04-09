"""
Unit tests for the collectionprocessor module.
"""

import mock
import os
import unittest

import collectionprocessor
import config
from document.document import Document
from parser import documentparser
import structureextractor
import logger
import stringprocessor

def setUpModule():
    global mock_writer
    mock_writer = mock.MagicMock(name="Mock Reader Writer")
    with mock.patch("collectionprocessor.StringProcessor",
        autospec=stringprocessor.StringProcessor):
        global colproc
        colproc = collectionprocessor.CollectionProcessor(mock_writer)

@mock.patch("collectionprocessor.logger", autospec=logger)
class TestCollectionProcessor(unittest.TestCase):
    """Test the CollectionProcessor class.
    """
    @mock.patch("collectionprocessor.StringProcessor",
        autospec=stringprocessor.StringProcessor)
    @mock.patch("collectionprocessor.structureextractor",
        autospec=structureextractor)
    @mock.patch("collectionprocessor.os", autospec=os)
    def test_extract_record_metadata(self, mock_os, mock_strucex, mock_str_proc,
        mock_logger):
        """Test the extract_record_metadata method.
        """
        # Set up the input objects
        collection_dir = mock.create_autospec(str)
        docstruc_filename = mock.create_autospec(str)
        filename_extension = ".xml"
        files = ["file1.xml", "file2.XmL", "file3.foo", ".file4.xml"]

        # Configure the mock os
        mock_os.listdir.return_value = files
        mock_os.path.splitext.side_effect = os.path.splitext

        # Configure mock logger
        mock_logger.get.return_value = ""

        # Make the structure extractor return useful objects
        extracted_docs = [
            ("file1.xml", [mock.create_autospec(Document) for x in range(10)]),
            ("file2.XmL", [mock.create_autospec(Document) for x in range(10)])]

        def extract_docs(filename):
            for entry in extracted_docs:
                if entry[0] == filename:
                    return entry[1]
        
        mock_strucex_instance = mock_strucex.StructureExtractor("", "")
        mock_strucex_instance.extract.side_effect = extract_docs

        # Run the SUT
        colproc.extract_record_metadata(collection_dir, docstruc_filename,
            filename_extension)

        # logger.log() should have been called twice for each file like this
        log_calls = []
        for i in range(0, 2):
            log_calls.append(mock.call("finished_recording_text_and_metadata",
                "false", mock_logger.REPLACE))
            log_calls.append(mock.call("text_and_metadata_recorded", str(i + 1),
                mock_logger.UPDATE))
        log_calls.append(mock.call("finished_recording_text_and_metadata",
                "true", mock_logger.REPLACE))
        mock_logger.log.assert_has_calls(log_calls)

        # The extractor should have been called on each file
        strucex_calls = [mock.call(files[0]), mock.call(files[1])]
        for call in strucex_calls:
            self.failUnless(call in mock_strucex_instance.extract.\
                call_args_list)

        # The reader writer should be called on every extracted doc
        createdoc_calls = []
        num_done = 1
        for entry in extracted_docs:
            for doc in entry[1]:
                createdoc_calls.append(mock.call(doc, num_done))
            num_done += 1
        mock_writer.create_new_document.assert_has_calls(createdoc_calls)

        # And logger should have been called at the end
        

    @mock.patch("collectionprocessor.StringProcessor",
        autospec=stringprocessor.StringProcessor)
    @mock.patch("collectionprocessor.DocumentParser",
        autospec=documentparser.DocumentParser)
    def test_parse_documents(self, mock_dp, mock_str_proc, mock_logger):
        """Tests for the test_parse_documents method.
        """
        # Set up the mocks
        max_doc = 20
        mock_writer.list_document_ids.return_value = range(max_doc)
        mock_dp_instance = mock_dp("", "")

        mock_gotten_doc = mock.create_autospec(Document)
        mock_writer.get_document.return_value = mock_gotten_doc

        latest = 5
        mock_logger.get.return_value = str(latest)

        # Run the SUT
        colproc.parse_documents()

        # Reader writer should have been called for every id greater than
        # what the logger returned and once at the end
        get_doc_calls = [mock.call(x) for x in range(latest + 1, max_doc)]
        mock_writer.get_document.assert_has_calls(get_doc_calls)
        mock_writer.finish_grammatical_processing.assert_called_once()

        # Document parser should have been called on every doc
        parse_calls = [mock.call(mock_gotten_doc)
            for x in range(latest + 1, max_doc)]
        mock_dp_instance.parse_document.assert_has_calls(parse_calls)

        # Logger should be called twice per doc
        logger_calls = []
        for i in range(latest + 1, max_doc):
            logger_calls.append(mock.call("finished_grammatical_processing",
                "false", mock_logger.REPLACE))
            logger_calls.append(mock.call("latest_parsed_document_id",
                str(i), mock_logger.REPLACE))
        mock_logger.log.assert_has_calls(logger_calls)

    def test_calculate_index_sequences(self, mock_logger):
        pass

class TestCollectionProcessorProcess(unittest.TestCase):
    """Tests specifically for CollectionProcessor.process().
    """
    def setUp(self):
        colproc.calculate_index_sequences = mock.create_autospec(
            colproc.calculate_index_sequences)
            #name="calc_index_sequences",)
        colproc.parse_documents = mock.create_autospec(
            colproc.parse_documents)
            #name="parse_documents",)
        colproc.extract_record_metadata = mock.create_autospec(
            colproc.extract_record_metadata)
            #name="extract_record_metadata",)

        # Set up the dict that is our "logging database" and set the arguments
        # for calling process()
        self.log_dict = {"finished_recording_text_and_metadata": "true",
            "finished_grammatical_processing": "true",
            "finished_sequence_processing": "true",
            "word_counts_done": "true",
            "tfidf_done": "true",
            "word_similarity_calculations_done": "true"
        }
        
        self.args = ["", "", "", False]

        # Reset the previously used mocks
        mock_writer.reset_mock()

    @mock.patch("collectionprocessor.Database")
    def test_process_reset(self, mock_db):
        """Test that database reset works properly.
        """
        colproc.process("", "", "", True)

        mock_db.reset.assert_called_once()

    @mock.patch("collectionprocessor.config", autospec=config)
    @mock.patch("collectionprocessor.logger", autospec=logger)
    def test_process_e_r_m(self, mock_logger, mock_config):
        """Test that extract_record_metadata() is called properly.
        """
        mock_logger.get.side_effect = self.log_dict.__getitem__
        # Should just extract_record_metadata
        self.log_dict["finished_recording_text_and_metadata"] = "false"
        mock_config.SEQUENCE_INDEXING = False
        mock_config.PART_OF_SPEECH_TAGGING = False
        mock_config.GRAMMATICAL_PROCESSING = False
        colproc.process(*self.args)

        assert colproc.extract_record_metadata.called
        assert colproc.calculate_index_sequences.called == False
        assert colproc.parse_documents.called == False
        assert len(colproc.reader_writer.method_calls) == 0

    @mock.patch("collectionprocessor.config", autospec=config)
    @mock.patch("collectionprocessor.logger", autospec=logger)
    def test_process_parse_documents(self, mock_logger, mock_config):
        """Test that parse_documents is called properly
        """
        mock_logger.get.side_effect = self.log_dict.__getitem__

        # Should only run parse_documents
        self.log_dict["finished_grammatical_processing"] = "false"
        mock_config.SEQUENCE_INDEXING = False
        colproc.process(*self.args)

        assert colproc.parse_documents.call_count == 1
        assert colproc.calculate_index_sequences.called == False
        assert colproc.extract_record_metadata.called == False
        assert len(colproc.reader_writer.method_calls) == 0

    @mock.patch("collectionprocessor.logger", autospec=logger)
    def test_process_calc_index_sequences(self, mock_logger):
        """Test that calculate_index_sequences() is called along with
        the reader_writer.
        """
        mock_logger.get.side_effect = self.log_dict.__getitem__

        # Should run calculate_index_sequences() and run the reader_writer
        colproc.process(*self.args)

        assert colproc.calculate_index_sequences.call_count == 1
        assert mock_writer.finish_indexing_sequences.call_count == 1
        assert len(mock_writer.method_calls) == 1
        assert colproc.parse_documents.called == False
        assert colproc.extract_record_metadata.called == False

    @mock.patch("collectionprocessor.logger", autospec=logger)
    def test_process_calc_word_counts(self, mock_logger):
        """Test that ReaderWriter.calculate_word_counts() is called along with
        the logs being updated.
        """
        mock_logger.get.side_effect = self.log_dict.__getitem__

        self.log_dict["word_counts_done"] = "false"
        self.log_dict["finished_sequence_processing"] = "false"
        colproc.process(*self.args)

        assert mock_writer.calculate_word_counts.call_count == 1
        assert len(mock_writer.method_calls) == 1
        assert colproc.calculate_index_sequences.called == False
        assert colproc.parse_documents.called == False
        assert colproc.extract_record_metadata.called == False
        mock_logger.log.assert_called_once_with("word_counts_done", "true",
            mock_logger.REPLACE)

    @mock.patch("collectionprocessor.logger", autospec=logger)
    def test_process_tfidfs(self, mock_logger):
        """Test that ReaderWriter.calculate_tfidfs() is called.
        """
        mock_logger.get.side_effect = self.log_dict.__getitem__

        self.log_dict["tfidf_done"] = "false"
        self.log_dict["finished_sequence_processing"] = "false"
        colproc.process(*self.args)

        assert mock_writer.calculate_tfidfs.call_count == 1
        assert len(mock_writer.method_calls) == 1
        assert colproc.calculate_index_sequences.called == False
        assert colproc.parse_documents.called == False
        assert colproc.extract_record_metadata.called == False

    @mock.patch("collectionprocessor.logger", autospec=logger)
    def test_process_tfidfs(self, mock_logger):
        """Test that calculate_lin_similarities() is run.
        """
        mock_logger.get.side_effect = self.log_dict.__getitem__
        
        self.log_dict["word_similarity_calculations_done"] = "false"
        self.log_dict["finished_sequence_processing"] = "false"
        colproc.process(*self.args)

        assert mock_writer.calculate_lin_similarities.call_count == 1
        assert len(mock_writer.method_calls) == 1
        assert colproc.calculate_index_sequences.called == False
        assert colproc.parse_documents.called == False
        assert colproc.extract_record_metadata.called == False
