#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
using namespace std;

string tostr(long long unsigned int i)
{
	stringstream s;
	s<<i;
	return s.str();
}

int main(int argc, char** argv)
{
	if(argc != 2)
	{
		cout << "Usage: fastindex <reference.fasta>\n";
		return 0;
	}

	string reff = argv[1];

	ifstream in(argv[1],ifstream::in);

	if(!in)
	{
		return 1;
	}

	in.seekg(0,in.end);
	long long unsigned int length=in.tellg();
	in.seekg(0,in.beg);

	char* buffer=new char[length];

	in.read(buffer,length);
	
	if(!in)
	{
		length=in.gcount();
	}

	ofstream out_index((reff+".teaser.findex").c_str(),ofstream::out);
	ofstream out_contig((reff+".teaser.fcontig").c_str(),ofstream::out);

	string header = "{\"seqs\": [\n";
	out_index.write(header.c_str(),header.size());

	long long unsigned int contig_pos = 0;
	long long unsigned int curr_contig_start = 0;
	int internal_id=1;
	string seq_id="";

	const int contig_buffer_len=8192;
	int contig_buffer_pos=0;
	char contig_buffer[contig_buffer_len];

	bool stop=false;

	for(long long unsigned int i = 0; i < length; ++ i)
	{
		const char c = buffer[i];
		string id_buffer="";

		switch(c)
		{
			case '\n':
			case '\r':
				break;

			case '>':
				i++;
				while(i<length && buffer[i]!='\n' && buffer[i]!='\r')
				{
					id_buffer.push_back(buffer[i]);
					i++;
				}

				if(i==length)
				{
					stop=true;
					break;
				}
				
				if (seq_id.size())
				{
					string ostr="";

					if(internal_id>1) ostr=",\n";

					ostr+="{\"id\":\""+seq_id+"\", \"start\": "+tostr(curr_contig_start)+", \"end\": "+tostr(contig_pos)+", \"internal_id\": "+tostr(internal_id)+"}";
					out_index.write(ostr.c_str(),ostr.size());
					internal_id++;
				}

				seq_id = id_buffer;
				curr_contig_start = contig_pos;
				break;

			default:
				contig_buffer[contig_buffer_pos++]=c;
				contig_pos++;

				if(contig_buffer_pos == contig_buffer_len)
				{
					out_contig.write(contig_buffer,contig_buffer_len);
					contig_buffer_pos=0;
				}

				break;
		
		}

		if(stop)
			break;
	}

	if(seq_id.size())
	{
		string ostr="";

		if(internal_id>1) ostr=",\n";

		ostr+="{\"id\":\""+seq_id+"\", \"start\": "+tostr(curr_contig_start)+", \"end\": "+tostr(contig_pos)+", \"internal_id\": "+tostr(internal_id)+"}";
		out_index.write(ostr.c_str(),ostr.size());
		internal_id++;
	}


	if(contig_buffer_pos)
		out_contig.write(contig_buffer,contig_buffer_pos);

	string ostr="],\n\"contig_len\": " + tostr(contig_pos) + "}";
	out_index.write(ostr.c_str(),ostr.size());

	in.close();
	out_contig.close();
	out_index.close();

	return 0;	
	
}
