python3 -B ./basic_search/match/similarity_bert/Run.py \
    --model_name bert-match \
    --bert_type bert-base-chinese \
    --optimizer adamw \
    --dataset match-car-2 \
    --clf_label_dim 2 \
    --max_seq_len 32 \
    --batch_size 16 \
    --valset_ratio 0 \
    --epochs 300 \
    --patience 3 \
    --log_dir ../resouces/logs/search-match \
    --target_dir ../resouces/models/search-match/