# -*- coding: utf-8 -*-

import os
import sys

import torch
from torch.utils.data import DataLoader

sys.path.append('..') # TODO
# from modules.alpha_learner.nn_with_bert.function.modeling import BERT_Match
from modules.modules_args import opt
from modules.utils.tokenizer.bert import Tokenizer4Bert
from function.BERT_MATCH import BERT_Match
from Dataset import MatchDataset
from Utils import train, validate


def build_model():

    # -------------------- Model definition ------------------- #
    print(20 * "=", " Model Init", 20 * "=")
    print("\t", opt)

    print("\t* Building model...")
    tokenizer = Tokenizer4Bert(opt.local_bert_dir, opt.max_seq_len, True)
    # config = BertConfig.from_json_file(opt.local_bert_config_file)
    model = BERT_Match(opt).to(opt.device)
    checkpoint = None

    print(20 * "=", " Preparing for training ", 20 * "=")
    # 保存模型的路径
    if not os.path.exists(opt.target_dir):
        os.makedirs(opt.target_dir)

    # -------------------- Data loading ------------------- #
    print("\t* Loading training data...")
    train_set = MatchDataset(opt.dataset_file['train'], tokenizer, opt.label_dict, max_seq_len=opt.max_seq_len)
    train_loader = DataLoader(dataset=train_set, batch_size=opt.batch_size, shuffle=True)
    print("\t* Loading validation data...")
    val_set = MatchDataset(opt.dataset_file['val'], tokenizer, opt.label_dict, max_seq_len=opt.max_seq_len)
    val_loader = DataLoader(dataset=val_set, batch_size=opt.batch_size, shuffle=False)

    # -------------------- Preparation for training  ------------------- #
    # 待优化的参数
    param_optimizer = list(model.named_parameters())
    no_decay = ['bias', 'LayerNorm.bias', 'LayerNorm.weight']
    optimizer_grouped_parameters = [
            {
                    'params':[p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
                    'weight_decay':0.01
            },
            {
                    'params':[p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
                    'weight_decay':0.0
            }
    ]
    optimizer = opt.optimizer(optimizer_grouped_parameters, lr=opt.lr)
    #optimizer = torch.optim.Adam(optimizer_grouped_parameters, lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", 
                                                           factor=0.85, patience=opt.patience)
    best_score = 0.0
    start_epoch = 1
    # Data for loss curves plot
    epochs_count = []
    train_losses = []
    valid_losses = []
    # Continuing training from a checkpoint if one was given as argument
    if checkpoint:
        checkpoint = torch.load(checkpoint)
        start_epoch = checkpoint["epoch"] + 1
        best_score = checkpoint["best_score"]
        print("\t* Training will continue on existing model from epoch {}...".format(start_epoch))
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        epochs_count = checkpoint["epochs_count"]
        train_losses = checkpoint["train_losses"]
        valid_losses = checkpoint["valid_losses"]
     # Compute loss and accuracy before starting (or resuming) training.
    _, valid_loss, valid_accuracy, auc = validate(model, val_loader)
    print("\t* Validation loss before training: {:.4f}, accuracy: {:.4f}%, auc: {:.4f}".format(valid_loss, (valid_accuracy*100), auc))
    # -------------------- Training epochs ------------------- #
    print("\n", 20 * "=", "Training roberta model on device: {}".format(opt.device), 20 * "=")
    patience_counter = 0
    for epoch in range(start_epoch, opt.epochs + 1):
        epochs_count.append(epoch)
        print("* Training epoch {}:".format(epoch))
        epoch_time, epoch_loss, epoch_accuracy = train(model, train_loader, optimizer, epoch, opt.max_grad_norm)
        train_losses.append(epoch_loss)
        print("-> Training time: {:.4f}s, loss = {:.4f}, accuracy: {:.4f}%"
              .format(epoch_time, epoch_loss, (epoch_accuracy*100)))
        print("* Validation for epoch {}:".format(epoch))
        epoch_time, epoch_loss, epoch_accuracy , epoch_auc= validate(model, val_loader)
        valid_losses.append(epoch_loss)
        print("-> Valid. time: {:.4f}s, loss: {:.4f}, accuracy: {:.4f}%, auc: {:.4f}\n"
              .format(epoch_time, epoch_loss, (epoch_accuracy*100), epoch_auc))
        # Update the optimizer's learning rate with the scheduler.
        scheduler.step(epoch_accuracy)
        # Early stopping on validation accuracy.
        if epoch_accuracy < best_score:
            patience_counter += 1
        else:
            best_score = epoch_accuracy
            patience_counter = 0
            torch.save({"epoch": epoch, 
                        "model": model.state_dict(),
                        "best_score": best_score,
                        "epochs_count": epochs_count,
                        "train_losses": train_losses,
                        "valid_losses": valid_losses},
                        os.path.join(opt.target_dir, "best.pth.tar"))
        if patience_counter >= opt.patience:
            print("-> Early stopping: patience limit reached, stopping...")
            break
    
if __name__ == "__main__":

    build_model()
    test_model()
