#!/bin/bash

# INHOSP
echo "All ItemIDs"
python learn_classifier_db.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=metavision --drop
python learn_classifier_db.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=carevue --drop
echo "All CUIs"
python learn_classifier_db.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=metavision --map_to_CUI --drop --cui_method=all
python learn_classifier_db.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=carevue --map_to_CUI --drop --cui_method=all
echo "Spanning CUIs"
python learn_classifier_db.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=metavision --map_to_CUI --drop --cui_method=spanning
python learn_classifier_db.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=carevue --map_to_CUI --drop --cui_method=spanning
echo "Longest CUIs"
python learn_classifier_db.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=metavision --map_to_CUI --drop --cui_method=longest
python learn_classifier_db.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=carevue --map_to_CUI --drop --cui_method=longest


echo "Common Item IDs"
python learn_classifier_mv_cv.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=carevue --testdb=metavision --drop --intersection
python learn_classifier_mv_cv.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=metavision --testdb=carevue --drop --intersection
echo "All Item IDs"
python learn_classifier_mv_cv.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=carevue --testdb=metavision --drop
python learn_classifier_mv_cv.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=metavision --testdb=carevue --drop
echo "CUIs Spanning"
python learn_classifier_mv_cv.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=carevue --testdb=metavision --map_to_CUI --drop --cui_method=spanning
python learn_classifier_mv_cv.py --penalty=l2 --outcome=inhosp --filter_threshold=4 --traindb=metavision --testdb=carevue --map_to_CUI --drop --cui_method=spanning


# #PROLONGED LOS
echo "All Item IDs" 
python learn_classifier_db.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=metavision --drop
python learn_classifier_db.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=carevue --drop
echo "All CUIs"
python learn_classifier_db.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=metavision --map_to_CUI --drop --cui_method=all
python learn_classifier_db.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=carevue --map_to_CUI --drop --cui_method=all
echo "Spanning CUIs"
python learn_classifier_db.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=metavision --map_to_CUI --drop --cui_method=spanning
python learn_classifier_db.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=carevue --map_to_CUI --drop --cui_method=spanning
echo "Longest CUIs"
python learn_classifier_db.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=metavision --map_to_CUI --drop --cui_method=longest
python learn_classifier_db.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=carevue --map_to_CUI --drop --cui_method=longest

echo "Common Item IDs"
python learn_classifier_mv_cv.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=metavision --testdb=carevue --drop --intersection
python learn_classifier_mv_cv.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=carevue --testdb=metavision --drop --intersection
echo "All Item IDs"
python learn_classifier_mv_cv.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=metavision --testdb=carevue --drop
python learn_classifier_mv_cv.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=carevue --testdb=metavision --drop
echo "CUIs Spanning"
python learn_classifier_mv_cv.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=metavision --testdb=carevue --map_to_CUI --drop --cui_method=spanning
python learn_classifier_mv_cv.py --penalty=l2 --outcome=prolonged_los --filter_threshold=4 --traindb=carevue --testdb=metavision --map_to_CUI --drop --cui_method=spanning


echo "DONE"
