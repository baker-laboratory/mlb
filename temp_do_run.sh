#!/bin/bash


# Will you have to remake this file better


bench_type=$1
bench_which=$2
bench_method=$3

run_dir=runs/$bench_type/$bench_which/$bench_method
bench_dir=benchmarks/$bench_type/$bench_which
method_dir=methods/$bench_type/$bench_which/$bench_method


# rm -r $run_dir
mkdir -p $run_dir
cp -r $method_dir/* $run_dir
cp -r $bench_dir/* $run_dir

rm $run_dir/ml_benchmarks
ln -s $(readlink -f ./) $run_dir/ml_benchmarks

cd $run_dir
./run.sh
