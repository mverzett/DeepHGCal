from trainers.h3d_conv import H3dConvTrainer
import argparse


parser = argparse.ArgumentParser(description='Run training for recurrent cal')
parser.add_argument('input', help="Path to config file")
parser.add_argument('config', help="Config section within the config file")
parser.add_argument('--test', default=False, help="Whether to run evaluation on test set")
args = parser.parse_args()


trainer = H3dConvTrainer(args.input, args.config)

if args.test:
    trainer.test()
else:
    trainer.train()
