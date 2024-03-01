before_text = """\n<DATA_TITLE>=* A Distributed Proofreaders Canada eBook *= </DATA_TITLE>\n\n\n\n\n\n[Cover Illustration]\n\n\n\n\n\n\nNOVELS BY JAMES HILTON\n\n\n\n\nL O S T   H O R I Z O N\n\n\n\n\n\n\n<PROLOGUE><PROLOGUE_TITLE> PROLOGUE </PROLOGUE_TITLE>\n\n\n\n\nCigars had burned low, and we were beginning to sample the disillusionment...\n\n\n\n\n\n<CHAPTER><CHAPTER_TITLE> CHAPTER 1 </CHAPTER_TITLE>\n\nDuring that third week of May the situation in Baskul had become much worse...\n\n\n\n\n\n<CHAPTER><CHAPTER_TITLE> CHAPTER 2 </CHAPTER_TITLE>\n\nThe journey was expected to be long and perilous...\n\nThey shook hands, and Mallinson left.\n\n\n\nConway sat alone in the lantern-light. It seemed to him, in a phrase\nengraved on memory, that all the loveliest things were transient and\nperishable, that the two worlds were finally beyond reconciliation, and\nthat one of them hung, as always, by a thread. After he had pondered for\nsome time he looked at his watch; it was ten minutes to three.\n\n\n\n\n\n<EPILOGUE> EPILOGUE\n\n\nContinuing, he said: “The little fellow\nlooked at me solemnly for a moment, and then answered in that funny\nclipped English that the educated Chinese have—‘Oh no, she was most\nold—most old of anyone I have ever seen.’”\n\n\n\nWe sat for a long time in silence.\n\nWOODFORD GREEN\nApril 1933\n<THE_END> THE END </THE_END>\n_Printed in Great Britain by_ R. & R. CLARK, LIMITED, _Edinburgh_.\n\n\n\n\n<TRANSCRIBER_NOTES> TRANSCRIBER NOTES \n\nMisspelled words and printer errors have been corrected. Where multiple\nspellings occur, majority use has been employed.\n\n\n[The end of _Lost Horizon_ by James Hilton]\n"""

correct_text = """\n<DATA_TITLE>=* A Distributed Proofreaders Canada eBook *= </DATA_TITLE>\n\n\n\n\n\n[Cover Illustration]\n\n\n\n\n\n\nNOVELS BY JAMES HILTON\n\n\n\n\nL O S T   H O R I Z O N\n\n\n\n\n\n\n<PROLOGUE><PROLOGUE_TITLE> PROLOGUE </PROLOGUE_TITLE>\n\n\n\n\nCigars had burned low, and we were beginning to sample the disillusionment...\n\n\n\n\n\n<CHAPTER><CHAPTER_TITLE> CHAPTER 1 </CHAPTER_TITLE>\n\nDuring that third week of May the situation in Baskul had become much worse...\n\n\n\n\n\n</CHAPTER>\n<CHAPTER><CHAPTER_TITLE> CHAPTER 2 </CHAPTER_TITLE>\n\nThe journey was expected to be long and perilous...\n\nThey shook hands, and Mallinson left.\n\n\n\nConway sat alone in the lantern-light. It seemed to him, in a phrase\nengraved on memory, that all the loveliest things were transient and\nperishable, that the two worlds were finally beyond reconciliation, and\nthat one of them hung, as always, by a thread. After he had pondered for\nsome time he looked at his watch; it was ten minutes to three.\n\n\n\n\n\n</CHAPTER>\n</PROLOGUE>\n<EPILOGUE> EPILOGUE\n\n\nContinuing, he said: “The little fellow\nlooked at me solemnly for a moment, and then answered in that funny\nclipped English that the educated Chinese have—‘Oh no, she was most\nold—most old of anyone I have ever seen.’”\n\n\n\nWe sat for a long time in silence.\n\nWOODFORD GREEN\nApril 1933\n</EPILOGUE>\n<THE_END> THE END </THE_END>\n_Printed in Great Britain by_ R. & R. CLARK, LIMITED, _Edinburgh_.\n\n\n\n\n<TRANSCRIBER_NOTES> TRANSCRIBER NOTES \n\nMisspelled words and printer errors have been corrected. Where multiple\nspellings occur, majority use has been employed.\n\n\n[The end of _Lost Horizon_ by James Hilton]\n\n</TRANSCRIBER_NOTES>"""

from tag import auto_close_tags


def test_auto_close_tag():
    assert correct_text == auto_close_tags(before_text)
